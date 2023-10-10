import os
import random
from typing import Tuple

import numpy as np
import pandas as pd
from enforce_typing import enforce_types

from pdr_backend.predictoor.approach3.data_factory import DataFactory
from pdr_backend.predictoor.approach3.data_ss import DataSS
from pdr_backend.predictoor.approach3.mathutil import nmse
from pdr_backend.predictoor.approach3.model_factory import ModelFactory
from pdr_backend.predictoor.approach3.model_ss import ModelSS
from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3
from pdr_backend.predictoor.approach3.timeutil import (
    pretty_timestr,
    timestr_to_ut,
)
from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent


@enforce_types
class PredictoorAgent3(BasePredictoorAgent):
    predictoor_config_class = PredictoorConfig3

    def get_prediction(
        self, addr: str, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair. Info in self.feeds[addr]
          timestamp -- int -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth

        @notes
          Below is the default implementation, giving random predictions.
          You need to customize it to implement your own strategy.
        """
        feed = self.feeds[addr]
        data_ss = DataSS(
            csv_dir=os.path.abspath("pdr_backend/predictoor/approach3/csvs"),
            # 2019-09-13_04:00 earliest
            # TODO: ajust parameters
            st_timestamp=timestr_to_ut("2022-09-13"),
            # 'now','2023-06-21_17:55'
            fin_timestamp=timestr_to_ut("2023-06-24"),
            max_N_train=500,  # 50000 # if inf, only limited by data available
            N_test=100,  # 50000 . num points to test on, 1 at a time (online)
            Nt=2,  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
            usdcoin=feed.quote,
            timeframe=feed.timeframe,
            signals=["close"],  # ["open", "high","low", "close", "volume"],
            coins=[feed.base, feed.quote],
            exchange_ids=[feed.source],
            yval_exchange_id=feed.source,
            yval_coin=feed.base,
            yval_signal="close",
        )
        model_ss = ModelSS("LIN")
        trade_engine = TradeEngine(data_ss, model_ss)
        trade_engine._init_loop_attributes()
        trade_engine.run()

        # TODO: adjust, for the moment this is copied from approach1
        predval = bool(random.getrandbits(1))

        # Stake amount is in ETH
        stake = random.randint(1, 30) / 10

        return (predval, stake)


# TODO: class copied from tlmplay, needs to be renamed and repurposed
class TradeEngine:
    @enforce_types
    def __init__(
        self,
        data_ss: DataSS,
        model_ss: ModelSS,
    ):
        self.data_ss = data_ss
        self.model_ss = model_ss

        self.data_factory = DataFactory(self.data_ss)

        self._init_loop_attributes()

    @property
    def usdcoin(self) -> str:
        return self.data_ss.usdcoin

    @property
    def tokcoin(self) -> str:
        return self.data_ss.yval_coin

    @enforce_types
    def _init_loop_attributes(self):
        # TODO: unify logging or drop this
        # filebase = f'out_{current_ut()}.txt'

        """
        self.logfile = os.path.join(self.trade_ss.logpath, filebase)
        with open(self.logfile, 'w') as f:
            f.write('\n')
        """

        self.tot_profit_usd = 0.0
        self.nmses_train, self.ys_test, self.ys_testhat, self.corrects = [], [], [], []
        self.profit_usds, self.tot_profit_usds = [], []

    @enforce_types
    def run(self):
        self._init_loop_attributes()
        print("Start run")
        # main loop!
        hist_df = self.data_factory.get_hist_df()
        for test_i in range(self.data_ss.N_test):
            self.run_one_iter(test_i, hist_df)

        print("Done all iters.")

        nmse_train = np.average(self.nmses_train)
        nmse_test = nmse(self.ys_testhat, self.ys_test)
        print(f"Final nmse_train={nmse_train:.5f}, nmse_test={nmse_test:.5f}")

        self._final_plot()

    @enforce_types
    def run_one_iter(self, test_i: int, hist_df: pd.DataFrame):
        testshift = self.data_ss.N_test - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        X, y, var_with_prev, _ = self.data_factory.create_xy(hist_df, testshift)

        st, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st:fin, :], X[fin : fin + 1]
        y_train, y_test = y[st:fin], y[fin : fin + 1]

        # used for PREV model, that's all
        self.model_ss.var_with_prev = var_with_prev
        model_factory = ModelFactory(self.model_ss)
        model = model_factory.build(X_train, y_train)

        y_trainhat = model.predict(X_train)  # eg yhat=zhat[y-5]
        # plotutil.plot_vals_vs_time1(y_train, y_trainhat,"ytr & ytrhat vs time")
        # plotutil.scatter_pred_vs_actual(y_train, y_trainhat, "ytr vs ytrhat")

        nmse_train = nmse(y_train, y_trainhat, min(y), max(y))
        self.nmses_train.append(nmse_train)

        # current time
        ut = (
            int(hist_df.index.values[-1])
            - testshift * int(os.getenv("SECONDS_PER_EPOCH", 300)) * 1000
        )

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

        pred_dir = "UP" if predprice > curprice else "DN"
        true_dir = "UP" if trueprice > curprice else "DN"
        correct = pred_dir == true_dir
        correct_s = "Y" if correct else "N"
        self.corrects.append(correct)
        acc = float(sum(self.corrects)) / len(self.corrects) * 100
        print(
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
