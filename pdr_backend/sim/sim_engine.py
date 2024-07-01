import logging
import os
import uuid
from typing import Optional, Tuple

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
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_model import SimModel
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_predictoor import SimPredictoor
from pdr_backend.sim.sim_state import SimState
from pdr_backend.sim.sim_trader import SimTrader
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
        predict_feed = predict_train_feedset.predict
        assert predict_feed.signal == "close", \
            "only operates on close predictions"
        
        self.predict_train_feedset = predict_train_feedset
        self.ppss = ppss

        # can be disabled by calling disable_realtime_state()
        self.do_state_updates = True

        self.st = SimState()

        self.pdr = SimPredictoor(ppss.predictoor_ss)
        self.trader = SimTrader(ppss, predict_feed)

        self.sim_plotter = SimPlotter()

        self.logfile = ""

        if multi_id:
            self.multi_id = multi_id
        else:
            self.multi_id = str(uuid.uuid4())
            
        assert self.transform == "None"

    @property
    def predict_feed(self) -> ArgFeed:
        return self.predict_train_feedset.predict_feed

    @property
    def timeframe(self) -> ArgTimeframe:
        return self.predict_feed.timeframe

    @property
    def pdr_ss(self) -> PredictoorSS:
        return self.ppss.predictoor_ss
    
    @property
    def aimodel_ss_ss(self) -> AimodelSS:
        return self.pdr_ss.aimodel_ss
    
    @property
    def transform(self) -> str:
        return self.aimodel_ss.transform
    
    @property
    def others_stake(self) -> float:
        return self.others_stale.amt_eth
    
    @property
    def revenue(self) -> float:
        return self.pdr_ss.revenue.amt_eth

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

        # initialize
        self._init_loop_attributes()

        # ohclv data
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()
        
        # main loop!
        for test_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(test_i, mergedohlcv_df)

        # done
        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, test_i: int, mergedohlcv_df: pl.DataFrame):
        # build model
        st = self.st
        data_f = SimModelDataFactory(self.ppss)
        model_d: SimModelData = data_f.build(iter_i, mergdohlcv_df)
        model_f = SimModelFactory(self.aimodel_ss)
        if model_f.do_build(st.sim_model, test_i):
            st.sim_model = model_f.train(test_i, model_d)

        # make prediction
        sim_model_p: SimModelPrediction = self.model.predict_next()

        # predictoor takes action (stake)
        stake_up, stake_down = self.pdr.predict_iter(sim_model_p)

        # trader takes action (trade)
        trader_profit = self.trader.trade_iter(
            cur_close, cur_high, cur_low, sim_model_p,
        )

        # observe true price change
        true_up_close = next_close > cur_close
        true_up_UP = next_high > y_thr_UP    # did next high go > prev close+% ?
        true_up_DOWN = next_low < y_thr_DOWN # did next low  go < prev close-% ?

        # update state - classifier data
        st.classif_base.update(true_up_UP, true_up_DOWN, sim_model_p)
        st.classif_metrics.update(st.classif_base)

        # update predictoor profit
        st.profit.update_pdr_profit(
            others_stake, pdr_ss.others_stake_accuracy,
            stake_up, stake_down, true_up_close)
        
        # update trader profit
        self.profits.update_trader_profit(trader_profit)

        # log
        ut = self._calc_ut(mergedohlcv_df)
        SimLogLine(ppss, st, test_i, ut).log()

        # plot
        do_save_state, is_final_state = self._do_save_state(test_i)
        if do_save_state:
            d_UP = self._aimodel_plotdata_1dirn(UP)
            d_DOWN = self._aimodel_plotdata_1dirn(DOWN)
            d = {UP: d_UP, DOWN: d_DOWN}
            st.iter_number = test_i
            self.sim_plotter.save_state(st, d, is_final_state)

    @enforce_types
    def _aimodel_plotdata_1dir(self, dirn: Dirn) -> AimodelPlotdata:
        st = self.st
        model, model_data = st.sim_model[dirn], st.sim_model_data[dirn]
        colnames = model_data.colnames
        colnames = [shift_one_earlier(c) for c in colnames]
        most_recent_x = model_data.X[-1, :]
        slicing_x = most_recent_x
        d = AimodelPlotdata(
            model,
            model_data.X_train,
            model_data.ytrue_train,
            None,
            None,
            colnames,
            slicing_x,
        )
        return d

    @enforce_types
    def _recent_close(self, mergedohlcv_df, testshift: int) -> Tuple[float, float]:
        """@return -- (cur_close, next_close)"""
        p = self.predict_feed_trainset.predict_feed
        _, _, yraw_close, _, _ = data_f.create_xy(
            mergedohlcv_df,
            testshift,
            p.variant_close(),
            [p.variant_close()],
        )
        cur_close, next_close = yraw_close[-2], yraw_close[-1]
        return (cur_close, next_close)
    
    @enforce_types
    def _calc_ut(self, mergedohlcv_df) -> UnixTimeMs:
        recent_ut = UnixTimeMs(int(mergedohlcv_df["timestamp"].to_list()[-1]))
        ut = UnixTimeMs(recent_ut - testshift * self.timeframe.ms)
        return ut

    @enforce_types
    def disable_realtime_state(self):
        self.do_state_updates = False

    @enforce_types
    def _do_save_state(self, i: int) -> Tuple[bool, bool]:
        """For this iteration i, (a) save state? (b) is it final iteration?"""
        if self.ppss.sim_ss.is_final_iter(i):
            return True, True

        # don't save if disabled
        if not self.do_state_updates:
            return False, False

        # don't save first 5 iters -> not interesting
        # then save the next 5 -> "stuff's happening!"
        # then save every 5th iter, to balance "stuff's happening" w/ speed
        N = self.ppss.sim_ss.test_n
        do_update = i >= 5 and (i < 10 or i % 5 == 0 or (i + 1) == N)
        if not do_update:
            return False, False

        return True, False

