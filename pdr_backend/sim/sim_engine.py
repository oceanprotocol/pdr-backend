import logging
import os
import uuid
from typing import Optional

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

        self.model_high: Optional[Aimodel] = None
        self.model_low: Optional[Aimodel] = None

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
    def run(self):
        logger.info("Start run")
        self._init_loop_attributes()

        # main loop!
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()
        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss, st = self.ppss, self.ppss.predictoor_ss, self.st
        transform = pdr_ss.aimodel_data_ss.transform
        others_stake = pdr_ss.others_stake.amt_eth
        revenue = pdr_ss.revenue.amt_eth

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(pdr_ss)  # type: ignore[arg-type]
        predict_feed = self.predict_train_feedset.predict
        train_feeds = self.predict_train_feedset.train_on

        # X, ycont, and x_df are all expressed in % change wrt prev candle
        p = predict_feed
        predict_feed_close = p
        predict_feed_high = ArgFeed(p.exchange, "high", p.pair, p.timeframe)
        predict_feed_low = ArgFeed(p.exchange, "low", p.pair, p.timeframe)
        _, _, yraw_close, _, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed_close,
            train_feeds,
        )
        X_high, ytran_high, yraw_high, x_df_high, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed_high,
            train_feeds,
        )
        X_low, ytran_low, yraw_low, _, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed_low,
            train_feeds,
        )
        colnames_high = list(x_df_high.columns)

        cur_close, next_close = yraw_close[-2], yraw_close[-1]
        cur_high, next_high = yraw_high[-2], yraw_high[-1]
        cur_low, _ = yraw_low[-2], yraw_low[-1]

        st_, fin = 0, X_high.shape[0] - 1
        X_train_high, X_test_high = X_high[st_:fin, :], X_high[fin : fin + 1, :]
        ytran_train_high, _ = ytran_high[st_:fin], ytran_high[fin : fin + 1]
        X_train_low, X_test_low = X_low[st_:fin, :], X_low[fin : fin + 1, :]
        ytran_train_low, _ = ytran_low[st_:fin], ytran_low[fin : fin + 1]

        percent_change_needed = 0.002  # magic number. TODO: move to ppss.yaml
        if transform == "None":
            y_thr_high = cur_close * (1 + percent_change_needed)
            y_thr_low = cur_close * (1 - percent_change_needed)
        else:  # transform = "RelDiff"
            y_thr_high = +np.std(yraw_close) * percent_change_needed
            y_thr_low = -np.std(yraw_close) * percent_change_needed
        ytrue_high = data_f.ycont_to_ytrue(ytran_high, y_thr_high)
        ytrue_low = data_f.ycont_to_ytrue(ytran_low, y_thr_low)

        ytrue_train_high, _ = ytrue_high[st_:fin], ytrue_high[fin : fin + 1]
        ytrue_train_low, _ = ytrue_low[st_:fin], ytrue_low[fin : fin + 1]

        if (
            self.model_high is None
            or self.st.iter_number % pdr_ss.aimodel_ss.train_every_n_epochs == 0
        ):
            model_f = AimodelFactory(pdr_ss.aimodel_ss)
            self.model_high = model_f.build(
                X_train_high,
                ytrue_train_high,
                ytran_train_high,
                y_thr_high,
            )
            self.model_low = model_f.build(
                X_train_low,
                ytrue_train_low,
                ytran_train_low,
                y_thr_low,
            )

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        timeframe: ArgTimeframe = predict_feed.timeframe  # type: ignore
        ut = UnixTimeMs(recent_ut - testshift * timeframe.ms)

        # predict price direction
        prob_up: float = self.model_high.predict_ptrue(X_test_high)[0]
        prob_down: float = 1.0 - self.model_low.predict_ptrue(X_test_low)[0]  # type: ignore
        if (prob_up + prob_down) > 1.0:  # ensure predictions don't conflict
            prob_up = prob_up / (prob_up + prob_down)
            prob_down = 1.0 - prob_up
        conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
        conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
        conf_threshold = self.ppss.trader_ss.sim_confidence_threshold
        pred_up: bool = prob_up > 0.5 and conf_up > conf_threshold
        pred_down: bool = prob_down > 0.5 and conf_down > conf_threshold
        st.probs_up.append(prob_up)
        st.ytrues_hat.append(prob_up > 0.5)

        # predictoor: (simulate) submit predictions with stake
        acct_up_profit = acct_down_profit = 0.0
        max_stake_amt = pdr_ss.stake_amount.amt_eth
        assert (prob_up + prob_down) <= 1.0
        stake_up = max_stake_amt * prob_up
        stake_down = max_stake_amt * prob_down
        acct_up_profit -= stake_up
        acct_down_profit -= stake_down

        trader_profit = self.trader.trade_iter(
            cur_close,
            pred_up,
            pred_down,
            conf_up,
            conf_down,
            cur_high,
            cur_low,
        )

        st.trader_profits_USD.append(trader_profit)

        # observe true price change
        true_up_close = next_close > cur_close

        if transform == "None":
            true_up_high = next_high > y_thr_high
        else:
            raise NotImplementedError("build me")
        st.ytrues.append(true_up_high)

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
        if self.model_high.do_regr:
            pred_ycont = self.model_high.predict_ycont(X_test_high)[0]
            if transform == "None":
                pred_next_close = pred_ycont
            else:  # transform = "RelDiff"
                relchange = pred_ycont
                pred_next_close = cur_close + relchange * cur_close
            yerr = next_close - pred_next_close

        st.aim.update(acc_est, acc_l, acc_u, f1, precision, recall, loss, yerr)

        # track predictoor profit
        tot_stake = others_stake + stake_up + stake_down
        others_stake_correct = others_stake * pdr_ss.others_accuracy
        if true_up_close:
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
            cs_ = [shift_one_earlier(c_) for c_ in colnames_high]
            most_recent_x = X_high[-1, :]
            slicing_x = most_recent_x  # plot about the most recent x
            d = AimodelPlotdata(
                self.model_high,
                X_train_high,
                ytrue_train_high,
                ytran_train_high,
                y_thr_high,
                cs_,
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
