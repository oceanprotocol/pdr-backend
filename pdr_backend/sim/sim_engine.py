import logging
import os
from typing import Optional

from enforce_typing import enforce_types
import polars as pl
from statsmodels.stats.proportion import proportion_confint as calc_CI

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.xycsv import XycsvMgr
from pdr_backend.aimodel.ycont_to_ytrue import ycont_to_ytrue
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_state import SimState
from pdr_backend.sim.sim_trader import SimTrader
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("sim_engine")


# pylint: disable=too-many-instance-attributes
class SimEngine:
    @enforce_types
    def __init__(
        self,
        ppss: PPSS,
        predict_train_feedset: PredictTrainFeedset,
    ):
        self.predict_train_feedset = predict_train_feedset
        assert isinstance(self.predict_feed, ArgFeed)
        assert self.predict_feed.signal == "close", "only operates on close predictions"
        self.ppss = ppss

        self.st = SimState()

        self.trader = SimTrader(ppss, self.predict_feed)

        self.runid = str(UnixTimeMs.now())  # eg "1738232779406"
        self.xycsv_mgr = XycsvMgr(ppss.sim_ss.xy_dir, self.runid)
        self.logfile = ""

        # timestamp -> prob up
        self.model: Optional[Aimodel] = None

    @property
    def predict_feed(self) -> ArgFeed:
        return self.predict_train_feedset.predict

    @enforce_types
    def _init_loop_attributes(self):
        filebase = f"out_{self.runid}.txt"
        self.logfile = os.path.join(self.ppss.sim_ss.log_dir, filebase)

        fh = logging.FileHandler(self.logfile)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

    @enforce_types
    def run(self, mergedohlcv_df: Optional[pl.DataFrame] = None):
        logger.info("Start run")
        self._init_loop_attributes()

        if mergedohlcv_df is None:
            f = OhlcvDataFactory(self.ppss.lake_ss)
            mergedohlcv_df = f.get_mergedohlcv_df()

        # main loop!
        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        ppss, pdr_ss, st = self.ppss, self.ppss.predictoor_ss, self.st

        testshift = ppss.sim_ss.test_n - test_i - 1  # eg [99, 98, .., 2, 1, 0]
        data_f = AimodelDataFactory(pdr_ss)  # type: ignore[arg-type]
        predict_feed = self.predict_train_feedset.predict
        train_feeds = self.predict_train_feedset.train_on

        # y is [sample_i]:float. Larger sample_i --> newer
        # X is [sample_i,var_i]:float. Larger var_i --> newer

        X, y, _, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed,
            train_feeds,
        )

        cur_close, next_close = y[-2], y[-1]
        cur_high, cur_low = data_f.get_highlow(mergedohlcv_df, predict_feed, testshift)

        if ppss.sim_ss.transform == "center_on_recent":
            for sample_i in range(X.shape[0]):
                sample_i_close = X[sample_i, -1]  # make everything rel. to this
                X[sample_i, :] = (X[sample_i, :] - sample_i_close) / sample_i_close
                y[sample_i] = (y[sample_i] - sample_i_close) / sample_i_close
            X = X[:, :-1]  # remove the far-right column of zeroes
            y_thr = 0.0
        else:
            y_thr = cur_close

        self.xycsv_mgr.save_xy(X, y, st.iter_number)

        st_, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st_:fin, :], X[fin : fin + 1, :]
        y_train, _ = y[st_:fin], y[fin : fin + 1]

        ytrue = ycont_to_ytrue(y, y_thr)

        ytrue_train, _ = ytrue[st_:fin], ytrue[fin : fin + 1]

        if (
            self.model is None
            or st.iter_number % pdr_ss.aimodel_ss.train_every_n_epochs == 0
        ):
            model_f = AimodelFactory(pdr_ss.aimodel_ss)
            self.model = model_f.build(X_train, ytrue_train, y_train, y_thr)

        # current time
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        timeframe: ArgTimeframe = predict_feed.timeframe  # type: ignore
        ut = UnixTimeMs(recent_ut - testshift * timeframe.ms)

        # predict price direction
        prob_up: float = float(self.model.predict_ptrue(X_test)[0])  # in [0.0, 1.0]
        prob_down: float = 1.0 - prob_up
        conf_up = max(0, (prob_up - 0.5) * 2.0)  # to range [0,1]
        conf_down = max(0, (prob_down - 0.5) * 2.0)  # to range [0,1]
        conf_threshold = self.ppss.trader_ss.sim_confidence_threshold
        pred_up: bool = prob_up > 0.5 and conf_up > conf_threshold
        pred_down: bool = prob_up < 0.5 and conf_down > conf_threshold

        # trade
        profit = self.trader.trade_iter(
            cur_close,
            pred_up,
            pred_down,
            conf_up,
            conf_down,
            cur_high,
            cur_low,
        )
        did_trade = profit != 0

        # observe true
        true_up = next_close > cur_close

        # update state
        self.st.cum_profit += profit
        if did_trade:
            self.st.num_trades += 1
            self.st.num_correct_pred_in_trade += int(true_up == pred_up)
        self.st.num_correct_pred_all += int(true_up == pred_up)

        # log
        conf = max(conf_up, conf_down)
        self._log_line(test_i, ut, prob_up, conf, profit)

        # wrap up loop
        st.iter_number += 1

    @enforce_types
    def _log_line(self, test_i, ut, prob_up, conf, profit):
        s = f"Iter #{test_i+1}/{self.ppss.sim_ss.test_n}"
        s += f" ut={ut}"
        s += f" dt={ut.to_timestr()[:-7]}"

        s += " ║"
        s += f" prob_up={prob_up:.3f}"
        s += f", conf={conf:.3f}"

        s += " ║"
        count, nobs = self.st.num_correct_pred_all, (test_i + 1)
        acc, (l, u) = count / nobs, calc_CI(count=count, nobs=nobs)
        s += f" acc={acc*100:5.2f}% [{l*100:5.2f}%, {u*100:5.2f}%]"
        if self.st.num_trades > 0:
            count, nobs = self.st.num_correct_pred_in_trade, self.st.num_trades
            acc, (l, u) = count / nobs, calc_CI(count=count, nobs=nobs)
            s += f", trades acc={acc*100:5.2f}% [{l*100:5.2f}%, {u*100:5.2f}%]"
        else:
            s += f", trades acc={'N/A':5s}% [{'N/A':5s}%, {'N/A':5s}%]"

        s += " ║"
        perc_trade = self.st.num_trades / (test_i + 1)
        s += f" # trades={self.st.num_trades:4d} ({perc_trade*100:6.2f}%)"

        s += " ║"
        s += f" tdr_profit=${profit:6.2f}"
        s += f" (cumul ${self.st.cum_profit:6.2f})"

        logger.info(s)
