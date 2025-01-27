import logging
import os
import uuid
from typing import Optional

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_factory import AimodelFactory
from pdr_backend.aimodel.ycont_to_ytrue import ycont_to_ytrue
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.sim.sim_trader import SimTrader
from pdr_backend.sim.sim_state import SimState
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

        self.st = SimState()

        self.trader = SimTrader(ppss, self.predict_feed)

        self.logfile = ""

        if multi_id:
            self.multi_id = multi_id
        else:
            self.multi_id = str(uuid.uuid4())

        # timestamp -> prob up
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

        # X, ycont, and x_df are all expressed in % change wrt prev candle
        X, y, _, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            predict_feed,
            train_feeds,
        )

        st_, fin = 0, X.shape[0] - 1
        X_train, X_test = X[st_:fin, :], X[fin : fin + 1, :]
        y_train, _ = y[st_:fin], y[fin : fin + 1]

        cur_high, cur_low = data_f.get_highlow(mergedohlcv_df, predict_feed, testshift)

        cur_close = y[-2]

        y_thr = cur_close
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
        prob_up: float = self.model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        prob_down: float = 1.0 - prob_up
        conf_up = (prob_up - 0.5) * 2.0  # to range [0,1]
        conf_down = (prob_down - 0.5) * 2.0  # to range [0,1]
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

        # update state
        st.probs_up.append(prob_up)
        st.profits.append(profit)

        # log
        self._log_line(test_i, ut)

        # save state
        self.save_state(test_i, self.ppss.sim_ss.test_n)

    def _log_line(self, test_i, ut):
        s = f"Iter #{test_i+1}/{self.ppss.sim_ss.test_n}"
        s += f" ut={ut}"
        s += f" dt={ut.to_timestr()[:-7]}"
        s += " ║"

        s += f" prob_up={self.st.probs_up[-1]:.3f}"

        s += " ║"

        s += f" tdr_profit=${self.st.profits[-1]:6.2f}"
        s += f" (cumul ${sum(self.st.profits):6.2f})"

        logger.info(s)

    @enforce_types
    def save_state(self, i: int, N: int):
        "Save state on this iteration Y/N?"
        if self.ppss.sim_ss.is_final_iter(i):
            return True, True

        # don't save first 5 iters -> not interesting
        # then save the next 5 -> "stuff's happening!"
        # then save every 5th iter, to balance "stuff's happening" w/ speed
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return False, False

        return True, False
