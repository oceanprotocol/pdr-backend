import os
from typing import List

from enforce_typing import enforce_types
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pdr_backend.simulation.constants import MS_PER_EPOCH
from pdr_backend.simulation.data_factory import DataFactory
from pdr_backend.simulation.data_ss import DataSS
from pdr_backend.simulation.model_factory import ModelFactory
from pdr_backend.simulation.model_ss import ModelSS
from pdr_backend.simulation.timeutil import current_ut, pretty_timestr
from pdr_backend.simulation.tradeutil import TradeParams, TradeSS
from pdr_backend.util.mathutil import nmse


class PlotState:
    def __init__(self):
        self.fig, self.ax = plt.subplots()

        matplotlib.rcParams.update({"font.size": 22})
        plt.ion()
        plt.show()


# pylint: disable=too-many-instance-attributes
class TradeEngine:
    @enforce_types
    def __init__(
        self,
        data_ss: DataSS,
        model_ss: ModelSS,
        trade_pp: TradeParams,
        trade_ss: TradeSS,
    ):
        self.data_ss = data_ss
        self.model_ss = model_ss
        self.trade_pp = trade_pp
        self.trade_ss = trade_ss

        self.holdings = self.trade_pp.init_holdings
        self.tot_profit_usd = 0.0
        self.nmses_train: List[float] = []
        self.ys_test: List[float] = []
        self.ys_testhat: List[float] = []
        self.corrects: List[bool] = []
        self.profit_usds: List[float] = []
        self.tot_profit_usds: List[float] = []

        self.data_factory = DataFactory(self.data_ss)

        self.logfile = ""

        self.plot_state = PlotState()

    @property
    def usdcoin(self) -> str:
        return self.data_ss.usdcoin

    @property
    def tokcoin(self) -> str:
        return self.data_ss.yval_coin

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{current_ut()}.txt"
        self.logfile = os.path.join(self.trade_ss.logpath, filebase)
        with open(self.logfile, "w") as f:
            f.write("\n")

        self.tot_profit_usd = 0.0
        self.nmses_train, self.ys_test, self.ys_testhat, self.corrects = [], [], [], []
        self.profit_usds, self.tot_profit_usds = [], []

    @enforce_types
    def run(self):
        self._init_loop_attributes()
        log = self._log
        log("Start run")
        # main loop!
        hist_df = self.data_factory.get_hist_df()
        for test_i in range(self.data_ss.N_test):
            self.run_one_iter(test_i, hist_df)
            self._plot(test_i, self.data_ss.N_test)

        log("Done all iters.")

        nmse_train = np.average(self.nmses_train)
        nmse_test = nmse(self.ys_testhat, self.ys_test)
        log(f"Final nmse_train={nmse_train:.5f}, nmse_test={nmse_test:.5f}")

    @enforce_types
    def run_one_iter(self, test_i: int, hist_df: pd.DataFrame):
        log = self._log
        testshift = self.data_ss.N_test - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        X, y, var_with_prev, _ = self.data_factory.create_xy(hist_df, testshift)

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, y_test = y[st:fin], y[fin : fin + 1]

        self.model_ss.var_with_prev = var_with_prev  # used for PREV model, that's all
        model_factory = ModelFactory(self.model_ss)
        model = model_factory.build(X_train, y_train)

        y_trainhat = model.predict(X_train)  # eg yhat=zhat[y-5]

        nmse_train = nmse(y_train, y_trainhat, min(y), max(y))
        self.nmses_train.append(nmse_train)

        # current time
        ut = int(hist_df.index.values[-1]) - testshift * MS_PER_EPOCH

        # current price
        curprice = y_train[-1]

        # predict price
        predprice = model.predict(X_test)[0]
        self.ys_testhat.append(predprice)

        # simulate buy. Buy 'amt_usd' worth of TOK if we think price going up
        usdcoin_holdings_before = self.holdings[self.usdcoin]
        if self._do_buy(predprice, curprice):
            self._buy(curprice, self.trade_ss.buy_amt_usd)

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
        log(
            f"Iter #{test_i+1:3}/{self.data_ss.N_test}: "
            f" ut{pretty_timestr(ut)[9:][:-9]}"
            # f". Predval|true|err {predprice:.2f}|{trueprice:.2f}|{err:6.2f}"
            f". Preddir|true|correct = {pred_dir}|{true_dir}|{correct_s}"
            f". Total correct {sum(self.corrects):3}/{len(self.corrects):3}"
            f" ({acc:.1f}%)"
            # f". Spent ${amt_usdcoin_sell:9.2f}, recd ${amt_usdcoin_recd:9.2f}"
            f", profit ${profit_usd:7.2f}"
            f", tot_profit ${self.tot_profit_usd:9.2f}"
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

        p = self.trade_pp.fee_percent
        usdcoin_amt_fee = p * usdcoin_amt_sent
        tokcoin_amt_recd = (1 - p) * usdcoin_amt_sent / price
        self.holdings[self.tokcoin] += tokcoin_amt_recd

        self._log(
            f"  TX: BUY : send {usdcoin_amt_sent:8.2f} {self.usdcoin:4}"
            f", receive {tokcoin_amt_recd:8.2f} {self.tokcoin:4}"
            f", fee = {usdcoin_amt_fee:8.4f} {self.usdcoin:4}"
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

        p = self.trade_pp.fee_percent
        usdcoin_amt_fee = p * tokcoin_amt_sent * price
        usdcoin_amt_recd = (1 - p) * tokcoin_amt_sent * price
        self.holdings[self.usdcoin] += usdcoin_amt_recd

        self._log(
            f"  TX: SELL: send {tokcoin_amt_sent:8.2f} {self.tokcoin:4}"
            f", receive {usdcoin_amt_recd:8.2f} {self.usdcoin:4}"
            f", fee = {usdcoin_amt_fee:8.4f} {self.usdcoin:4}"
        )

    @enforce_types
    def _plot(self, i, N):
        if not self.trade_ss.do_plot:
            return

        # don't plot first 5 iters -> not interesting
        # then plot the next 5 -> "stuff's happening!"
        # then plot every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return

        fig, ax = self.plot_state.fig, self.plot_state.ax

        y = self.tot_profit_usds
        ylabel = "tot profit"

        HEIGHT = 8  # magic number
        WIDTH = HEIGHT * 2  # magic number

        N = len(y)
        x = list(range(0, N))
        ax.set_title(ylabel + " vs time")
        ax.plot(x, y, "g-")
        plt.ylabel(ylabel)
        plt.xlabel("time")
        fig.set_size_inches(WIDTH, HEIGHT)
        plt.pause(0.001)

    @enforce_types
    def _log(self, s: str):
        """Log to both stdout and to file"""
        print(s)
        with open(self.logfile, "a") as f:
            f.write(s + "\n")
