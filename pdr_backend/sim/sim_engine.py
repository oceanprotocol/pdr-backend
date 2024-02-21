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
from pdr_backend.util.time_types import UnixTimeMilliseconds


logger = logging.getLogger("sim_engine")
FONTSIZE = 12


@enforce_types
class PlotState:
    def __init__(self):
        self.fig, (self.ax0, self.ax1) = plt.subplots(2)
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
        self.tot_profit_usd = 0.0
        self.nmses_train: List[float] = []
        self.ys_test: List[float] = []
        self.ys_testhat: List[float] = []
        self.corrects: List[bool] = []
        self.profit_usds: List[float] = []
        self.tot_profit_usds: List[float] = []

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
        filebase = f"out_{UnixTimeMilliseconds.now()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.tot_profit_usd = 0.0
        self.nmses_train, self.ys_test, self.ys_testhat, self.corrects = [], [], [], []
        self.profit_usds, self.tot_profit_usds = [], []

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
        testshift = self.ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        model_data_factory = AimodelDataFactory(self.ppss.predictoor_ss)
        X, y, _, _ = model_data_factory.create_xy(mergedohlcv_df, testshift)

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, y_test = y[st:fin], y[fin : fin + 1]

        aimodel_factory = AimodelFactory(self.ppss.predictoor_ss.aimodel_ss)
        model = aimodel_factory.build(X_train, y_train)

        y_trainhat = model.predict(X_train)  # eg yhat=zhat[y-5]

        nmse_train = nmse(y_train, y_trainhat, min(y), max(y))
        self.nmses_train.append(nmse_train)

        # current time
        recent_ut = UnixTimeMilliseconds(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMilliseconds(
            recent_ut - testshift * self.ppss.predictoor_ss.timeframe_ms
        )

        # current price
        curprice = y_train[-1]

        # predict price
        predprice = model.predict(X_test)[0]
        self.ys_testhat.append(predprice)

        # simulate buy. Buy 'amt_usd' worth of TOK if we think price going up
        usdcoin_holdings_before = self.holdings[self.usdcoin]
        if self._do_buy(predprice, curprice):
            self._buy(curprice, self.ppss.trader_ss.buy_amt_usd)

        # observe true price
        trueprice = y_test[0]
        self.ys_test.append(trueprice)

        # simulate sell. Update tot_profit_usd
        tokcoin_amt_sell = self.holdings[self.tokcoin]
        if tokcoin_amt_sell > 0:
            self._sell(trueprice, tokcoin_amt_sell)
        usdcoin_holdings_after = self.holdings[self.usdcoin]

        profit_usd = usdcoin_holdings_after - usdcoin_holdings_before

        self.tot_profit_usd += profit_usd
        self.profit_usds.append(profit_usd)
        self.tot_profit_usds.append(self.tot_profit_usd)

        # err = abs(predprice - trueprice)
        pred_dir = "UP" if predprice > curprice else "DN"
        true_dir = "UP" if trueprice > curprice else "DN"
        correct = pred_dir == true_dir
        correct_s = "Y" if correct else "N"
        self.corrects.append(correct)
        acc = float(sum(self.corrects)) / len(self.corrects) * 100
        logger.info(
            "Iter #%d/%d: ut%s."
            ". Preddir|true|correct = %s|%s|%s"
            ". Total correct %d/%d"
            " (%.1f%%)"
            ", profit $%7.2f}"
            ", tot_profit $%9.2f",
            test_i + 1,
            self.ppss.sim_ss.test_n,
            ut.pretty_timestr()[9:][:-9],
            pred_dir,
            true_dir,
            correct_s,
            sum(self.corrects),
            len(self.corrects),
            acc,
            profit_usd,
            self.tot_profit_usd,
        )

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

        fig, ax0, ax1 = self.plot_state.fig, self.plot_state.ax0, self.plot_state.ax1

        y0 = self.tot_profit_usds
        N = len(y0)
        x = list(range(0, N))
        ax0.plot(x, y0, "g-")
        ax0.set_title(
            f"Trading profit vs time. Current: ${y0[-1]:.2f}",
            fontsize=FONTSIZE,
            fontweight="bold",
        )
        ax0.set_xlabel("time", fontsize=FONTSIZE)
        ax0.set_ylabel("trading profit (USD)", fontsize=FONTSIZE)

        y1_est, y1_l, y1_u = [], [], []  # est, 95% confidence intervals
        for i_ in range(N):
            n_correct = sum(self.corrects[: i_ + 1])
            n_trials = len(self.corrects[: i_ + 1])
            l, u = proportion_confint(count=n_correct, nobs=n_trials)
            y1_est.append(n_correct / n_trials * 100)
            y1_l.append(l * 100)
            y1_u.append(u * 100)

        ax1.cla()
        ax1.plot(x, y1_est, "b")
        ax1.fill_between(x, y1_l, y1_u, color="b", alpha=0.15)
        now_s = f"{y1_est[-1]:.2f}% [{y1_l[-1]:.2f}%, {y1_u[-1]:.2f}%]"
        ax1.set_title(
            f"% correct vs time. Current: {now_s}",
            fontsize=FONTSIZE,
            fontweight="bold",
        )
        ax1.set_xlabel("time", fontsize=FONTSIZE)
        ax1.set_ylabel("% correct", fontsize=FONTSIZE)

        HEIGHT = 8  # magic number
        WIDTH = HEIGHT * 2  # magic number
        fig.set_size_inches(WIDTH, HEIGHT)
        fig.tight_layout(pad=1.0)  # add space between plots
        plt.pause(0.001)
