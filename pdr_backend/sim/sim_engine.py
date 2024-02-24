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
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")
FONTSIZE = 9


# pylint: disable=too-many-instance-attributes
class SimEngineState:
    def __init__(self, init_holdings: dict):
        self.holdings: dict = init_holdings
        self.nmses_train: List[float] = []
        self.ys_test: List[float] = []
        self.ys_testhat: List[float] = []
        self.corrects: List[bool] = []
        self.trader_profits_USD: List[float] = []
        self.predictoor_profits_OCEAN: List[float] = []

        self.y2: List[float] = []


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

        self.ppss = ppss

        self.st = SimEngineState(
            copy.copy(self.ppss.trader_ss.init_holdings),
        )

        self.plot_state = None
        if self.ppss.sim_ss.do_plot:
            self.plot_state = PlotState()

        self.logfile = ""

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
        filebase = f"out_{UnixTimeMs.now()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.st.nmses_train, self.st.ys_test, self.st.ys_testhat, self.st.corrects = (
            [],
            [],
            [],
            [],
        )
        self.st.trader_profits_USD = []  # profit per epoch
        self.st.predictoor_profits_OCEAN = []  # profit per epoch

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

        nmse_train = np.average(self.st.nmses_train)
        nmse_test = nmse(self.st.ys_testhat, self.st.ys_test)
        logger.info("Final nmse_train=%.5f, nmse_test=%.5f", nmse_train, nmse_test)

    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        # pylint: disable=too-many-statements
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
        self.st.nmses_train.append(nmse_train)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMs(recent_ut - testshift * self.ppss.predictoor_ss.timeframe_ms)

        # current price
        curprice = y_train[-1]

        # predict price
        predprice = model.predict(X_test)[0]
        self.st.ys_testhat.append(predprice)

        # simulate buy. Buy 'amt_usd' worth of TOK if we think price going up
        usdcoin_holdings_before = self.st.holdings[self.usdcoin]
        if self._do_buy(predprice, curprice):
            self._buy(curprice, ppss.trader_ss.buy_amt_usd)

        # observe true price
        trueprice = y_test[0]
        self.st.ys_test.append(trueprice)

        # simulate sell. Update trader_profits_USD
        tokcoin_amt_sell = self.st.holdings[self.tokcoin]
        if tokcoin_amt_sell > 0:
            self._sell(trueprice, tokcoin_amt_sell)
        usdcoin_holdings_after = self.st.holdings[self.usdcoin]

        trader_profit_USD = usdcoin_holdings_after - usdcoin_holdings_before
        self.st.trader_profits_USD.append(trader_profit_USD)

        # err = abs(predprice - trueprice)
        pred_dir = "UP" if predprice > curprice else "DN"
        true_dir = "UP" if trueprice > curprice else "DN"
        correct = pred_dir == true_dir
        correct_s = "Y" if correct else "N"
        self.st.corrects.append(correct)

        # Update predictoor_profits_OCEAN
        if correct:
            others_stake_correct = pdr_ss.others_accuracy * pdr_ss.others_stake
            tot_stake_correct = others_stake_correct + pdr_ss.stake_amount
            percent_to_me = pdr_ss.stake_amount / tot_stake_correct
            predictoor_profit_OCEAN = percent_to_me * pdr_ss.revenue
        else:
            percent_to_me = 0
            predictoor_profit_OCEAN = -pdr_ss.stake_amount
        self.st.predictoor_profits_OCEAN.append(predictoor_profit_OCEAN)

        # Log
        n_correct, n_trials = sum(self.st.corrects), len(self.st.corrects)
        acc_est = float(n_correct) / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)

        s = f"Iter #{test_i+1}/{ppss.sim_ss.test_n}: "
        s += f"ut={ut.pretty_timestr()[9:][:-10]}"

        s += f". pred={pred_dir}, true={true_dir}, correct={correct_s}"
        s += f", %_rev_to_pdr={percent_to_me*100.0:7.4f}%"
        s += f" -> {predictoor_profit_OCEAN:8.5f} OCEAN profit"
        s += f" (cumulative {sum(self.st.predictoor_profits_OCEAN):7.2f} OCEAN)"

        s += f". Correct: {n_correct:4d}/{n_trials:4d} "
        s += f"= {acc_est*100:.2f}%"
        s += f" [{acc_l*100:.2f}%, {acc_u*100:.2f}%]"

        s += f". trading made ${trader_profit_USD:9.4f}"
        s += f" (cumulative ${sum(self.st.trader_profits_USD):9.4f})"
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
        usdcoin_amt_sent = min(usdcoin_amt_spend, self.st.holdings[self.usdcoin])
        self.st.holdings[self.usdcoin] -= usdcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * usdcoin_amt_sent
        tokcoin_amt_recd = (1 - p) * usdcoin_amt_sent / price
        self.st.holdings[self.tokcoin] += tokcoin_amt_recd

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
        self.st.holdings[self.tokcoin] -= tokcoin_amt_sent

        p = self.ppss.trader_ss.fee_percent
        usdcoin_amt_fee = p * tokcoin_amt_sent * price
        usdcoin_amt_recd = (1 - p) * tokcoin_amt_sent * price
        self.st.holdings[self.usdcoin] += usdcoin_amt_recd

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

    def _plot(self, i: int, N: int):
        if not self.ppss.sim_ss.do_plot:
            return

        # don't plot first 5 iters -> not interesting
        # then plot the next 5 -> "stuff's happening!"
        # then plot every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return

        self.plot_state.do_plot(self.st)  # type: ignore[union-attr]


@enforce_types
class PlotState:
    def __init__(self):
        self.fig, self.axs = plt.subplots(2, 2, gridspec_kw={"width_ratios": [3, 1]})
        self.x = []
        self.y0 = []
        self.y1_est, self.y1_l, self.y1_u = [], [], []
        self.jitter = []
        self.plotted_before = False
        self.y2 = []
        plt.ion()
        plt.show()

    # pylint: disable=too-many-statements
    def do_plot(self, st: SimEngineState):
        fig, ((ax0, ax1), (ax2, ax3)) = self.fig, self.axs

        N = len(st.predictoor_profits_OCEAN)
        N_done = len(self.x)

        # set x
        self.x = list(range(0, N))
        next_x = _slice(self.x, N_done, N)
        next_hx = [next_x[0], next_x[-1]]  # horizontal x

        # plot 0: predictoor profit vs time
        self.y0 = list(np.cumsum(st.predictoor_profits_OCEAN))
        next_y0 = _slice(self.y0, N_done, N)
        ax0.plot(next_x, next_y0, color="green")
        ax0.plot(next_hx, [0, 0], color="0.2", linestyle="dashed", linewidth=1)
        _set_title(ax0, f"Predictoor profit vs time. Current:{self.y0[-1]:.2f} OCEAN")
        if not self.plotted_before:
            ax0.set_ylabel("predictoor profit (OCEAN)", fontsize=FONTSIZE)
            ax0.set_xlabel("time", fontsize=FONTSIZE)
            _label_on_right(ax0)
            ax0.margins(0.005, 0.05)

        # plot 1: % correct vs time
        for i_ in range(N_done, N):
            n_correct = sum(st.corrects[: i_ + 1])
            n_trials = len(st.corrects[: i_ + 1])
            l, u = proportion_confint(count=n_correct, nobs=n_trials)
            self.y1_est.append(n_correct / n_trials * 100)
            self.y1_l.append(l * 100)
            self.y1_u.append(u * 100)
        next_y1_est = _slice(self.y1_est, N_done, N)
        next_y1_l = _slice(self.y1_l, N_done, N)
        next_y1_u = _slice(self.y1_u, N_done, N)

        ax1.plot(next_x, next_y1_est, "green")
        _ = ax1.fill_between(next_x, next_y1_l, next_y1_u, color="0.9")
        ax1.plot(next_hx, [50, 50], color="0.2", linestyle="dashed", linewidth=1)
        ax1.set_ylim(bottom=40, top=60)
        now_s = f"{self.y1_est[-1]:.2f}% [{self.y1_l[-1]:.2f}%, {self.y1_u[-1]:.2f}%]"
        _set_title(ax1, f"% correct vs time. Current: {now_s}")
        if not self.plotted_before:
            ax1.set_xlabel("time", fontsize=FONTSIZE)
            ax1.set_ylabel("% correct", fontsize=FONTSIZE)
            _label_on_right(ax1)
            ax1.margins(0.01, 0.01)

        # plot 2: trader profit vs time
        self.y2 = list(np.cumsum(st.trader_profits_USD))
        next_y2 = _slice(self.y2, N_done, N)
        ax2.plot(next_x, next_y2, color="blue")
        ax2.plot(next_hx, [0, 0], color="0.2", linestyle="dashed", linewidth=1)
        _set_title(ax2, f"Trader profit vs time. Current: ${self.y2[-1]:.2f}")
        if not self.plotted_before:
            ax2.set_xlabel("time", fontsize=FONTSIZE)
            ax2.set_ylabel("trader profit (USD)", fontsize=FONTSIZE)
            _label_on_right(ax2)
            ax2.margins(0.005, 0.05)

        # plot 3: 1d scatter of profits
        while len(self.jitter) < N:
            self.jitter.append(np.random.uniform())
        next_jitter = _slice(self.jitter, N_done, N)
        next_profits = _slice(st.trader_profits_USD, N_done, N)
        ax3.scatter(next_jitter, next_profits, color="blue", s=1)
        avg = np.average(st.trader_profits_USD)
        _set_title(ax3, f"Trader profit distribution. avg=${avg:.2f}")
        if not self.plotted_before:
            ax3.plot(
                [0 - 1, 1 + 1], [0, 0], color="0.2", linestyle="dashed", linewidth=1
            )
            ax3.set_ylabel("trader profit (USD)", fontsize=FONTSIZE)
            _label_on_right(ax3)
            plt.tick_params(bottom=False, labelbottom=False)
            ax3.margins(0.05, 0.05)

        # final pieces
        HEIGHT = 7.5  # magic number
        WIDTH = int(HEIGHT * 3)  # magic number
        fig.set_size_inches(WIDTH, HEIGHT)
        fig.tight_layout(pad=0.5, h_pad=1.0, w_pad=1.0)
        plt.pause(0.001)
        self.plotted_before = True


def _set_title(ax, s: str):
    ax.set_title(s, fontsize=FONTSIZE, fontweight="bold")


def _slice(a: list, N_done: int, N: int) -> list:
    return [a[i] for i in range(max(0, N_done - 1), N)]


def _label_on_right(ax):
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position("right")


def _del_lines(ax):
    for l in ax.lines:
        l.remove()
