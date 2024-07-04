import logging
import os
import uuid
from typing import Optional, Tuple

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel_data_factory import AimodelDataFactory
from pdr_backend.aimodel.aimodel_plotdata import AimodelPlotdata
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.lake.ohlcv_data_factory import OhlcvDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.sim.constants import Dirn, UP, DOWN
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_model_data_factory import SimModelDataFactory
from pdr_backend.sim.sim_model_factory import SimModelFactory
from pdr_backend.sim.sim_model_prediction import SimModelPrediction
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_predictoor import SimPredictoor
from pdr_backend.sim.sim_state import HistProfits, SimState
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
        multi_id: Optional[str] = None,
    ):
        self.ppss = ppss

        assert self.predict_feed.signal == "close", "only operates on close predictions"

        # can be disabled by calling disable_realtime_state()
        self.do_state_updates = True

        self.st = SimState()

        self.sim_predictoor = SimPredictoor(ppss.predictoor_ss)
        self.sim_trader = SimTrader(ppss)

        self.sim_plotter = SimPlotter()

        self.logfile = ""

        if multi_id:
            self.multi_id = multi_id
        else:
            self.multi_id = str(uuid.uuid4())

        assert self.pdr_ss.aimodel_data_ss.transform == "None"

    @property
    def pdr_ss(self) -> PredictoorSS:
        return self.ppss.predictoor_ss

    @property
    def predict_feed(self) -> ArgFeed:
        return self.pdr_ss.predict_train_feedsets[0].predict

    @property
    def timeframe(self) -> ArgTimeframe:
        assert self.predict_feed.timeframe is not None
        return self.predict_feed.timeframe

    @property
    def others_stake(self) -> float:
        return self.pdr_ss.others_stake.amt_eth

    @property
    def others_accuracy(self) -> float:
        return self.pdr_ss.others_accuracy

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
        for iter_i in range(self.ppss.sim_ss.test_n):
            self.run_one_iter(iter_i, mergedohlcv_df)

        # done
        logger.info("Done all iters.")

    # pylint: disable=too-many-statements# pylint: disable=too-many-statements
    @enforce_types
    def run_one_iter(self, iter_i: int, mergedohlcv_df: pl.DataFrame):
        # base data
        st = self.st
        df = mergedohlcv_df
        sim_model_data_f = SimModelDataFactory(self.ppss)
        testshift = sim_model_data_f.testshift(iter_i)

        # observe current price value, and related thresholds for classifier
        cur_close = self._curval(df, testshift, "close")
        cur_high = self._curval(df, testshift, "high")
        cur_low = self._curval(df, testshift, "low")
        y_thr_UP = sim_model_data_f.thr_UP(cur_close)
        y_thr_DOWN = sim_model_data_f.thr_DOWN(cur_close)

        # build model
        model_factory = SimModelFactory(self.pdr_ss.aimodel_ss)
        st.sim_model_data = sim_model_data_f.build(iter_i, df)
        if model_factory.do_build(st.sim_model, iter_i):
            st.sim_model = model_factory.build(st.sim_model_data)

        # make prediction
        predprob = self.st.sim_model.predict_next(st.sim_model_data.X_test)

        conf_thr = self.ppss.trader_ss.sim_confidence_threshold
        sim_model_p = SimModelPrediction(conf_thr, predprob[UP], predprob[DOWN])

        # predictoor takes action (stake)
        stake_up, stake_down = self.sim_predictoor.predict_iter(sim_model_p)

        # trader takes action (trade)
        trader_profit_USD = self.sim_trader.trade_iter(
            cur_close,
            cur_high,
            cur_low,
            sim_model_p,
        )

        # observe next price values
        next_close = self._nextval(df, testshift, "close")
        next_high = self._nextval(df, testshift, "high")
        next_low = self._nextval(df, testshift, "low")

        # observe price change prev -> next, and related changes for classifier
        trueval_up_close = next_close > cur_close
        trueval = {
            UP: next_high > y_thr_UP,  # did next high go > prev close+% ?
            DOWN: next_low < y_thr_DOWN,  # did next low  go < prev close-% ?
        }

        # calc predictoor profit
        pdr_profit_OCEAN = calc_pdr_profit(
            self.others_stake,
            self.others_accuracy,
            stake_up,
            stake_down,
            self.revenue,
            trueval_up_close,
        )

        # update state
        st.update(trueval, predprob, pdr_profit_OCEAN, trader_profit_USD)

        # log
        ut = self._calc_ut(df, testshift)
        SimLogLine(self.ppss, self.st, iter_i, ut).log()

        # plot
        do_save_state, is_final_state = self._do_save_state(iter_i)
        if do_save_state:
            d = self._aimodel_plotdata()
            st.iter_number = iter_i
            self.sim_plotter.save_state(st, d, is_final_state)

    @enforce_types
    def _aimodel_plotdata(self) -> dict:
        d_UP = self._aimodel_plotdata_1dir(UP)
        d_DOWN = self._aimodel_plotdata_1dir(DOWN)
        return {UP: d_UP, DOWN: d_DOWN}

    @enforce_types
    def _aimodel_plotdata_1dir(self, dirn: Dirn) -> AimodelPlotdata:
        st = self.st
        model = st.sim_model[dirn]
        model_data = st.sim_model_data[dirn]

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
            model_data.colnames,
            slicing_x,
        )
        return d

    @enforce_types
    def _curval(self, df, testshift: int, signal_str: str) -> float:
        # float() so not np.float64, bc applying ">" gives np.bool -> problems
        return float(self._yraw(df, testshift, signal_str)[-2])

    @enforce_types
    def _nextval(self, df, testshift: int, signal_str: str) -> float:
        # float() so not np.float64, bc applying ">" gives np.bool -> problems
        return float(self._yraw(df, testshift, signal_str)[-1])

    @enforce_types
    def _yraw(self, mergedohlcv_df, testshift: int, signal_str: str):
        assert signal_str in ["close", "high", "low"]
        feed = self.predict_feed.variant_signal(signal_str)
        aimodel_data_f = AimodelDataFactory(self.pdr_ss)
        _, _, yraw, _, _ = aimodel_data_f.create_xy(
            mergedohlcv_df,
            testshift,
            feed,
            ArgFeeds([feed]),
        )
        return yraw

    @enforce_types
    def _calc_ut(self, mergedohlcv_df, testshift: int) -> UnixTimeMs:
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

@enforce_types
def calc_pdr_profit(
    others_stake: float,
    others_accuracy: float,
    stake_up: float,
    stake_down: float,
    revenue: float,
    true_up_close: bool,
):
    assert others_stake >= 0
    assert 0.0 <= others_accuracy <= 1.0
    assert stake_up >= 0.0
    assert stake_down >= 0.0
    assert revenue >= 0.0

    amt_sent = stake_up + stake_down
    others_stake_correct = others_stake * others_accuracy
    tot_stake = others_stake + stake_up + stake_down
    if true_up_close:
        tot_stake_correct = others_stake_correct + stake_up
        percent_to_me = stake_up / tot_stake_correct
        amt_received = (revenue + tot_stake) * percent_to_me
    else:
        tot_stake_correct = others_stake_correct + stake_down
        percent_to_me = stake_down / tot_stake_correct
        amt_received = (revenue + tot_stake) * percent_to_me
    pdr_profit_OCEAN = amt_received - amt_sent
    return pdr_profit_OCEAN
