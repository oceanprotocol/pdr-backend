import logging
import os
import uuid
import time
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
from pdr_backend.sim.sim_logger import SimLogLine
from pdr_backend.sim.sim_plotter import SimPlotter
from pdr_backend.sim.sim_trader import SimTrader
from pdr_backend.sim.sim_state import SimState
from pdr_backend.util.strutil import shift_one_earlier
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.subgraph.subgraph_feed_contracts import query_feed_contracts
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.gql_data_factory import GQLDataFactory

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

        self.crt_trained_model: Optional[Aimodel] = None
        self.prediction_dataset: Optional[Dict[int, float]] = None
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
    def run(self):
        logger.info("Start run")
        self._init_loop_attributes()

        # main loop!
        f = OhlcvDataFactory(self.ppss.lake_ss)
        mergedohlcv_df = f.get_mergedohlcv_df()

        # fetch predictions data
        if not self.ppss.sim_ss.use_own_model:
            chain_prediction_data = self._get_past_predictions_from_chain(self.ppss)
            if not chain_prediction_data:
                return

            self.prediction_dataset = self._get_prediction_dataset(
                UnixTimeMs(self.ppss.lake_ss.st_timestamp).to_seconds(),
                UnixTimeMs(self.ppss.lake_ss.fin_timestamp).to_seconds(),
            )

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

        # predict price direction
        print("worked here")
        if self.ppss.sim_ss.use_own_model is not False:
            prob_up: float = self.model.predict_ptrue(X_test)[0]  # in [0.0, 1.0]
        else:
            ut_seconds = ut.to_seconds()
            if (
                self.prediction_dataset is not None
                and ut_seconds in self.prediction_dataset
            ):
                # check if the current slot is in the keys
                prob_up = self.prediction_dataset[ut_seconds]
            else:
                return

        print("prob_up--->", prob_up)
        prob_down: Optional[float] = 1.0 - prob_up
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

    @enforce_types
    def _get_prediction_dataset(
        self, start_slot: int, end_slot: int
    ) -> Dict[int, Optional[float]]:
        contracts = query_feed_contracts(
            self.ppss.web3_pp.subgraph_url,
            self.ppss.web3_pp.owner_addrs,
        )

        sPE = 300 if self.predict_feed.timeframe == "5m" else 3600
        # Filter contracts with the correct token pair and timeframe
        contract_to_use = [
            addr
            for addr, feed in contracts.items()
            if feed.symbol
            == f"{self.predict_feed.pair.base_str}/{self.predict_feed.pair.quote_str}"
            and feed.seconds_per_epoch == sPE
        ]

        query = f"""
            SELECT
                slot,
                CASE
                    WHEN roundSumStakes = 0.0 THEN NULL
                    WHEN roundSumStakesUp = 0.0 THEN NULL
                    ELSE roundSumStakesUp / roundSumStakes
                END AS probUp
            FROM
                pdr_payouts
            WHERE
                slot > {start_slot}
                AND slot < {end_slot}
                AND ID LIKE '{contract_to_use[0]}%'
        """

        print("self.ppss.lake_ss.lake_dir--->", self.ppss.lake_ss.lake_dir)
        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        df: pl.DataFrame = db.query_data(query)

        result_dict = {}

        print(df)
        for i in range(len(df)):
            if df["probUp"][i] is not None:
                result_dict[df["slot"][i]] = df["probUp"][i]

        return result_dict

    def _get_past_predictions_from_chain(self, ppss: PPSS):
        # calculate needed data start date
        current_time_s = int(time.time())
        timeframe = ppss.trader_ss.feed.timeframe
        number_of_data_points = ppss.sim_ss.test_n
        start_date = current_time_s - (timeframe.s * number_of_data_points)

        # check if ppss is correctly configured for data ferching
        # if start_date < int(
        #    UnixTimeMs.from_timestr(self.ppss.lake_ss.st_timestr) / 1000
        # ):
        #    logger.info(
        #        (
        #            "Lake dates configuration doesn't meet the requirements. "
        #            "Make sure you set start date before %s"
        #        ),
        #        time.strftime("%Y-%m-%d", time.localtime(start_date)),
        #    )
        #    return False

        # fetch data from subgraph
        gql_data_factory = GQLDataFactory(ppss)
        gql_data_factory._update()
        time.sleep(3)

        # check if required data exists in the data base
        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        query = """
        (SELECT timestamp
            FROM pdr_payouts
            ORDER BY timestamp ASC
            LIMIT 1)
            UNION ALL
            (SELECT timestamp
            FROM pdr_payouts
            ORDER BY timestamp DESC
            LIMIT 1);
        """
        data = db.query_data(query)
        if len(data["timestamp"]) < 2:
            logger.info(
                "No prediction data found in database at %s", self.ppss.lake_ss.lake_dir
            )
            return False
        start_timestamp = data["timestamp"][0] / 1000
        # end_timestamp = data["timestamp"][1] / 1000

        if start_timestamp > start_date:
            logger.info(
                (
                    "Not enough predictions data in the lake. "
                    "Make sure you fetch data starting from %s up to today"
                ),
                time.strftime("%Y-%m-%d", time.localtime(start_date)),
            )
            return False

        # if (end_timestamp + timeframe.s) < time.time():
        #    logger.info("Lake data is not up to date.")
        #    return False

        return True
