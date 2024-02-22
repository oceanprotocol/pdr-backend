import copy
import logging
import os
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import polars as pl
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.mathutil import nmse
from pdr_backend.util.timeutil import current_ut_ms, pretty_timestr

logger = logging.getLogger("sim_engine")
FONTSIZE = 11


@enforce_types
class PlotState:
    def __init__(self):
        self.fig, (self.ax0, self.ax1, self.ax2) = plt.subplots(3)
        plt.ion()
        plt.show()


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    def __init__(self, ppss: PPSS):
        # preconditions
        predict_feed = ppss.predictoor_ss.feed

        # timeframe doesn't need to match
        assert (
            str(predict_feed.exchange),
            str(predict_feed.pair),
        ) in ppss.predictoor_ss.aimodel_ss.exchange_pair_tups

        # pp & ss values
        self.ppss = ppss

        # state
        self.holdings = copy.copy(self.ppss.trader_ss.init_holdings)
        self.nmses_train: List[float] = []
        self.ys_test: List[float] = []
        self.ys_testhat: List[float] = []
        self.corrects: List[bool] = []
        self.trader_profits_USD: List[float] = []
        self.predictoor_profits_OCEAN: List[float] = []

        self.logfile = ""

        self.plot_state = None
        if self.ppss.sim_ss.do_plot:
            self.plot_state = PlotState()

        self.exchange = self.ppss.predictoor_ss.feed.ccxt_exchange(
            mock=self.ppss.sim_ss.tradetype in ["histmock", "histmock"],
            exchange_params=self.ppss.sim_ss.exchange_params,
        )

    @property
    def tokcoin(self) -> str:
        """Return e.g. 'ETH'"""
        return self.ppss.predictoor_ss.base_str

    @property
    def usdcoin(self) -> str:
        """Return e.g. 'USDT'"""
        return self.ppss.predictoor_ss.quote_str

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{current_ut_ms()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.nmses_train, self.ys_test, self.ys_testhat, self.corrects = [], [], [], []
        self.trader_profits_USD = [] # profit per epoch
        self.predictoor_profits_OCEAN = [] # profit per epoch

    @enforce_types
    def run(self):
        self._init_loop_attributes()
        logger.info("Start run")

        # main loop!
        pq_data_factory = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df: pl.DataFrame = pq_data_factory.get_mergedohlcv_df()
        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)
            self._plot(test_i, self.ppss.sim_ss.test_n)

        logger.info("Done all iters.")

        nmse_train = np.average(self.nmses_train)
        nmse_test = nmse(self.ys_testhat, self.ys_test)
        logger.info("Final nmse_train=%.5f, nmse_test=%.5f", nmse_train, nmse_test)

    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss = self.ppss, self.ppss.predictoor_ss
        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        model_data_factory = AimodelDataFactory(pdr_ss)
        X, y, _, _ = model_data_factory.create_xy(mergedohlcv_df, testshift)

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, y_test = y[st:fin], y[fin : fin + 1]

        aimodel_factory = AimodelFactory(pdr_ss.aimodel_ss)
        model = aimodel_factory.build(X_train, y_train)

        y_trainhat = model.predict(X_train)  # eg yhat=zhat[y-5]

        nmse_train = nmse(y_train, y_trainhat, min(y), max(y))
        self.nmses_train.append(nmse_train)

        # current time
        recent_ut = int(mergedohlcv_df["timestamp"].to_list()[-1])
        ut = recent_ut - testshift * pdr_ss.timeframe_ms

        # current price
        curprice = y_train[-1]

        # predict price
        predprice = model.predict(X_test)[0]
        self.ys_testhat.append(predprice)

        # simulate buy. Buy 'amt_usd' worth of TOK if we think price going up
        usdcoin_holdings_before = self.holdings[self.usdcoin]
        if self._do_buy(predprice, curprice):
            self._buy(curprice, ppss.trader_ss.buy_amt_usd)

        # observe true price
        trueprice = y_test[0]
        self.ys_test.append(trueprice)

        # simulate sell. Update trader_profits_USD
        tokcoin_amt_sell = self.holdings[self.tokcoin]
        if tokcoin_amt_sell > 0:
            self._sell(trueprice, tokcoin_amt_sell)
        usdcoin_holdings_after = self.holdings[self.usdcoin]

        trader_profit_USD = usdcoin_holdings_after - usdcoin_holdings_before
        self.trader_profits_USD.append(trader_profit_USD)
        
        # err = abs(predprice - trueprice)
        pred_dir = "UP" if predprice > curprice else "DN"
        true_dir = "UP" if trueprice > curprice else "DN"
        correct = pred_dir == true_dir
        correct_s = "Y" if correct else "N"
        self.corrects.append(correct)

        # Update predictoor_profits_OCEAN
        if correct:
            others_stake_correct = pdr_ss.others_accuracy * pdr_ss.others_stake
            percent_to_me = pdr_ss.stake_amount / others_stake_correct
            predictoor_profit_OCEAN = percent_to_me * pdr_ss.revenue
        else:
            predictoor_profit_OCEAN = -pdr_ss.stake_amount
        self.predictoor_profits_OCEAN.append(predictoor_profit_OCEAN)
        
        n_correct, n_trials = sum(self.corrects), len(self.corrects)
        acc_est = float(n_correct) / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        
        s = f"Iter #{test_i+1}/{ppss.sim_ss.test_n}: "
        s += f"ut{pretty_timestr(ut)[9:][:-7]}"
        
        s += f". Dir'n pred|true|correct? = {pred_dir}|{true_dir}|{correct_s}"
        s += f". Total correct {n_correct:4d}/{n_trials:4d} "
        s += f"= {acc_est*100:.2f}%"
        s += f" [{acc_l*100:.2f}%, {acc_u*100:.2f}%]"

        s += f". predictoor_profit [epoch {predictoor_profit_OCEAN:6.2f} OCEAN"
        s += f", total {sum(self.predictoor_profits_OCEAN):7.2f} OCEAN]"
        
        s += f". trader_profit [epoch ${trader_profit_USD:7.2f}"
        s += f", total ${sum(self.trader_profits_USD):8.2f}]"
        logger.info(s)

    def _do_buy(self, predprice: float, curprice: float) -> bool:
        """
        @arguments
          predprice -- predicted price (5 min from now)
          curprice -- current price (now)

        @return
          bool -- buy y/n?
        """
        return predprice > curprice

    def _buy(self, price: float, usdcoin_amt_spend: float):
        """
        @description
          Buy tokcoin with usdcoin

        @arguments
          price -- amt of usdcoin per token
          usdcoin_amt_spend -- amount to spend, in usdcoin; spend less if have less
        """
        # simulate buy
        usdcoin_amt_sent = min(usdcoin_amt_spend, self.holdings[self.usdcoin])
        self.holdings[self.usdcoin] -= usdcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * usdcoin_amt_sent
        tokcoin_amt_recd = (1 - p) * usdcoin_amt_sent / price
        self.holdings[self.tokcoin] += tokcoin_amt_recd

        self.exchange.create_market_buy_order(
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_recd
        )

        logger.info(
            "TX: BUY : send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            usdcoin_amt_sent,
            self.usdcoin,
            tokcoin_amt_recd,
            self.tokcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

    def _sell(self, price: float, tokcoin_amt_sell: float):
        """
        @description
          Sell tokcoin for usdcoin

        @arguments
          price -- amt of usdcoin per token
          tokcoin_amt_sell -- how much of coin to sell, in tokcoin
        """
        tokcoin_amt_sent = tokcoin_amt_sell
        self.holdings[self.tokcoin] -= tokcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * tokcoin_amt_sent * price
        usdcoin_amt_recd = (1 - p) * tokcoin_amt_sent * price
        self.holdings[self.usdcoin] += usdcoin_amt_recd

        self.exchange.create_market_sell_order(
            self.ppss.predictoor_ss.pair_str, tokcoin_amt_sent
        )

        logger.info(
            "TX: SELL: send %8.2f %s, receive %8.2f %s, fee = %8.4f %s",
            tokcoin_amt_sent,
            self.tokcoin,
            usdcoin_amt_recd,
            self.usdcoin,
            usdcoin_amt_fee,
            self.usdcoin,
        )

    @enforce_types
    def _plot(self, i, N):
        if not self.ppss.sim_ss.do_plot:
            return

        # don't plot first 5 iters -> not interesting
        # then plot the next 5 -> "stuff's happening!"
        # then plot every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return

        ps = self.plot_state
        fig, ax0, ax1, ax2 = ps.fig, ps.ax0, ps.ax1, ps.ax2
        
        N = len(self.predictoor_profits_OCEAN)
        x = list(range(0, N))

        # plot 0: % correct vs time
        y0_est, y0_l, y0_u = [], [], []  # est, 95% confidence intervals
        for i_ in range(N):
            n_correct = sum(self.corrects[: i_ + 1])
            n_trials = len(self.corrects[: i_ + 1])
            l, u = proportion_confint(count=n_correct, nobs=n_trials)
            y0_est.append(n_correct / n_trials * 100)
            y0_l.append(l * 100)
            y0_u.append(u * 100)
        
        ax0.cla()
        ax0.plot(x, y0_est, "b")
        ax0.fill_between(x, y0_l, y0_u, color="b", alpha=0.15)
        now_s = f"{y0_est[-1]:.2f}% [{y0_l[-1]:.2f}%, {y0_u[-1]:.2f}%]"
        ax0.set_title(
            f"% correct vs time. Current: {now_s}",
            fontsize=FONTSIZE,
            fontweight="bold",
        )
        ax0.set_xlabel("time", fontsize=FONTSIZE)
        ax0.set_ylabel("% correct", fontsize=FONTSIZE)

        # plot 1: predictoor profit vs time
        y1 = np.cumsum(self.predictoor_profits_OCEAN)
        ax1.plot(x, y1, "g-")
        ax1.set_title(
            f"Predictoor profit vs time. Current: ${y1[-1]:.2f}",
            fontsize=FONTSIZE,
            fontweight="bold",
        )
        ax1.set_xlabel("time", fontsize=FONTSIZE)
        ax1.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)

        # plot 2: trader profit vs time
        y2 = np.cumsum(self.trader_profits_USD)
        ax2.plot(x, y2, "g-")
        ax2.set_title(
            f"Trader profit vs time. Current: ${y2[-1]:.2f}",
            fontsize=FONTSIZE,
            fontweight="bold",
        )
        ax2.set_xlabel("time", fontsize=FONTSIZE)
        ax2.set_ylabel("trading profit (USD)", fontsize=FONTSIZE)

        # final pieces
        HEIGHT = 9  # magic number
        WIDTH = int(HEIGHT * 2)  # magic number
        fig.set_size_inches(WIDTH, HEIGHT)
        fig.tight_layout(pad=0.3)  # add space between plots
        plt.pause(0.001)
