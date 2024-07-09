#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os
import uuid
from typing import Optional, Dict

import numpy as np
import polars as pl
from enforce_typing import enforce_types
from sklearn.metrics import log_loss, precision_recall_fscore_support
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_chain_predictions import SimChainPredictions
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_trader import SimTrader
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.strutil import shift_one_earlier
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    def __init__(
        self,
        ppss: PPSS,
        predict_train_feedset: PredictTrainFeedset,
        multi_id: Optional[str] = None,
    ):
        self.predict_train_feedset = predict_train_feedset
        assert isinstance(self.predict_feed, ArgFeed)
        assert self.predict_feed.signal == "close", "only operates on close predictions"
        self.ppss = ppss

        # can be disabled by calling disable_realtime_state()
        self.do_state_updates = True

        self.st = SimState()

        self.trader = SimTrader(ppss, self.predict_feed)

        self.sim_plotter = SimPlotter()

        self.logfile = ""

        if multi_id:
            self.multi_id = multi_id
        else:
            self.multi_id = str(uuid.uuid4())

        # timestamp -> prob up
        self.chain_predictions_map: Dict[int, float] = {}
        self.model: Optional[Aimodel] = None

    @property
    def predict_feed(self) -> ArgFeed:
        return self.predict_train_feedset.predict

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{UnixTimeMs.now()}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

        self.st.init_loop_attributes()
        logger.info("Initialize plot data.")
        self.sim_plotter.init_state(self.multi_id)

    @enforce_types
    def load_chain_prediction_data(self):
        SimChainPredictions.verify_use_chain_data_in_syms_dependencies(self.ppss)
        if not SimChainPredictions.verify_prediction_data(self.ppss):
            raise Exception(
                "Could not get the required prediction data to run the simulations"
            )
        self.chain_predictions_map = SimChainPredictions.get_predictions_data(
            UnixTimeMs(self.ppss.lake_ss.st_timestamp).to_seconds(),
            UnixTimeMs(self.ppss.lake_ss.fin_timestamp).to_seconds(),
            self.ppss,
            self.predict_feed,
        )

    @enforce_types
    def run(self):
        logger.info("Start run")
        self._init_loop_attributes()

        # main loop!
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()

        # fetch predictions data
        if not self.ppss.sim_ss.use_own_model:
            self.load_chain_prediction_data()

        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss, st = self.ppss, self.ppss.predictoor_ss, self.st
        transform = pdr_ss.aimodel_data_ss.transform
        stake_amt = pdr_ss.stake_amount.amt_eth
        others_stake = pdr_ss.others_stake.amt_eth
        revenue = pdr_ss.revenue.amt_eth

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(pdr_ss)  # type: ignore[arg-type]
        predict_feed = self.predict_train_feedset.predict
        train_feeds = self.predict_train_feedset.train_on

        # X, ycont, and x_df are all expressed in % change wrt prev candle
        X, ytran, yraw, x_df, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed,
            train_feeds,
        )
        colnames = list(x_df.columns)

        st_, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st_:fin, :], X[fin : fin + 1, :]
        ytran_train, _ = ytran[st_:fin], ytran[fin : fin + 1]

        cur_high, cur_low = data_f.get_highlow(mergedohlcv_df, predict_feed, testshift)

        cur_close = yraw[-2]
        next_close = yraw[-1]

        if transform == "None":
            y_thr = cur_close
        else:  # transform = "RelDiff"
            y_thr = 0.0
        ytrue = data_f.ycont_to_ytrue(ytran, y_thr)

        ytrue_train, _ = ytrue[st_:fin], ytrue[fin : fin + 1]

        if (
            self.model is None
            or self.st.iter_number % pdr_ss.aimodel_ss.train_every_n_epochs == 0
        ):
            model_f = AimodelFactory(pdr_ss.aimodel_ss)
            self.model = model_f.build(X_train, ytrue_train, ytran_train, y_thr)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        timeframe: ArgTimeframe = predict_feed.timeframe  # type: ignore
        ut = UnixTimeMs(recent_ut - testshift * timeframe.ms)
        prob_up: float = 0.0
        # predict price direction
        if self.ppss.sim_ss.use_own_model:
            prob_up: float = self.model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        else:
            ut_seconds = ut.to_seconds()
            prediction = self.chain_predictions_map.get(ut_seconds)
            if prediction is None or type(prediction) is not float:
                logger.error("No prediction found at time %s", ut_seconds)
                return
            prob_up: float = prediction

        prob_down: float = 1.0 - prob_up
        conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
        conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
        conf_threshold = self.ppss.trader_ss.sim_confidence_threshold
        pred_up: bool = prob_up > 0.5 and conf_up > conf_threshold
        pred_down: bool = prob_up < 0.5 and conf_down > conf_threshold
        st.probs_up.append(prob_up)

        # predictoor: (simulate) submit predictions with stake
        acct_up_profit = acct_down_profit = 0.0
        stake_up = stake_amt * prob_up
        stake_down = stake_amt * (1.0 - prob_up)
        acct_up_profit -= stake_up
        acct_down_profit -= stake_down

        profit = self.trader.trade_iter(
            cur_close,
            pred_up,
            pred_down,
            conf_up,
            conf_down,
            cur_high,
            cur_low,
        )

        st.trader_profits_USD.append(profit)

        # observe true price
        true_up = next_close > cur_close
        st.ytrues.append(true_up)

        # update classifier metrics
        n_correct = sum(np.array(st.ytrues) == np.array(st.ytrues_hat))
        n_trials = len(st.ytrues)
        acc_est = n_correct / n_trials
        acc_l, acc_u = proportion_confint(count=n_correct, nobs=n_trials)
        (precision, recall, f1, _) = precision_recall_fscore_support(
            st.ytrues,
            st.ytrues_hat,
            average="binary",
            zero_division=0.0,
        )
        if min(st.ytrues) == max(st.ytrues):
            loss = 3.0
        else:
            loss = log_loss(st.ytrues, st.probs_up)
        yerr = 0.0
        if self.model.do_regr:
            pred_ycont = self.model.predict_ycont(X_test)[0]
            if transform == "None":
                pred_next_close = pred_ycont
            else:  # transform = "RelDiff"
                relchange = pred_ycont
                pred_next_close = cur_close + relchange * cur_close
            yerr = next_close - pred_next_close

        st.aim.update(acc_est, acc_l, acc_u, f1, precision, recall, loss, yerr)

        # track predictoor profit
        tot_stake = others_stake + stake_amt
        others_stake_correct = others_stake * pdr_ss.others_accuracy
        if true_up:
            tot_stake_correct = others_stake_correct + stake_up
            percent_to_me = stake_up / tot_stake_correct
            acct_up_profit += (revenue + tot_stake) * percent_to_me
        else:
            tot_stake_correct = others_stake_correct + stake_down
            percent_to_me = stake_down / tot_stake_correct
            acct_down_profit += (revenue + tot_stake) * percent_to_me
        pdr_profit_OCEAN = acct_up_profit + acct_down_profit
        st.pdr_profits_OCEAN.append(pdr_profit_OCEAN)

        SimLogLine(ppss, st, test_i, ut, acct_up_profit, acct_down_profit).log_line()

        save_state, is_final_state = self.save_state(test_i, self.ppss.sim_ss.test_n)

        if save_state:
            colnames = [shift_one_earlier(colname) for colname in colnames]
            most_recent_x = X[-1, :]
            slicing_x = most_recent_x  # plot about the most recent x
            d = AimodelPlotdata(
                self.model,
                X_train,
                ytrue_train,
                ytran_train,
                y_thr,
                colnames,
                slicing_x,
            )
            self.st.iter_number = test_i
            self.sim_plotter.save_state(self.st, d, is_final_state)

    def disable_realtime_state(self):
        self.do_state_updates = False

    @enforce_types
    def save_state(self, i: int, N: int):
        "Save state on this iteration Y/N?"
        if self.ppss.sim_ss.is_final_iter(i):
            return True, True

        # don't save if disabled
        if not self.do_state_updates:
            return False, False

        # don't save first 5 iters -> not interesting
        # then save the next 5 -> "stuff's happening!"
        # then save every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return False, False

        return True, False
