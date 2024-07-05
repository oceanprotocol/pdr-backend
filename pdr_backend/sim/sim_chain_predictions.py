import logging
import time
from typing import Dict, Optional
from enforce_typing import enforce_types
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs
import polars as pl


logger = logging.getLogger("sim_engine_chain_predictions")


class SimEngineChainPredictions:
    @staticmethod
    def get_predictions_data(
        start_slot: int, end_slot: int, ppss: PPSS, predict_feed: ArgFeed
    ) -> Dict[int, Optional[float]]:
        result_dict: Dict[int, Optional[float]] = {}
        db = DuckDBDataStore(ppss.lake_ss.lake_dir)
        query_cont = f"""
            SELECT
                contract
            FROM
                pdr_predictions
            WHERE
                timeframe = '{predict_feed.timeframe}'
                AND pair = '{predict_feed.pair.pair_str}'
            LIMIT 1
        """
        feed_contract_addr = db.query_data(query_cont)
        if len(feed_contract_addr) == 0:
            logger.error("Contract address for the given feed not found in database")
            return result_dict

        query = f"""
            SELECT
                slot,
                CASE
                    WHEN roundSumStakes = 0.0 THEN NULL
                    ELSE roundSumStakesUp / roundSumStakes
                END AS probUp
            FROM
                pdr_payouts
            WHERE
                slot > {start_slot}
                AND slot < {end_slot}
                AND ID LIKE '{feed_contract_addr.row(0)[0]}%'
        """

        df: pl.DataFrame = db.query_data(query)

        for row in df.to_dicts():
            if row["probUp"] is not None:
                result_dict[row["slot"]] = row["probUp"]

        return result_dict

    @staticmethod
    def verify_prediction_data(ppss: PPSS):
        # calculate needed data start date
        current_time_s = int(time.time())
        timeframe = ppss.trader_ss.feed.timeframe
        number_of_data_points = ppss.sim_ss.test_n
        start_date = current_time_s - (timeframe.s * number_of_data_points)

        # fetch data from subgraph
        try:
            gql_data_factory = GQLDataFactory(ppss)
            gql_data_factory._update()
        except Exception as e:
            logger.error("Fetching chain data failed. %s", e)

        # check if required data exists in the data base
        db = DuckDBDataStore(ppss.lake_ss.lake_dir)
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
        data: pl.DataFrame = db.query_data(query)

        if data.shape[0] > 0 and len(data["timestamp"]) < 2:
            logger.info(
                "No prediction data found in database at %s", ppss.lake_ss.lake_dir
            )
            return False
        start_timestamp = UnixTimeMs(data["timestamp"][0]).to_seconds()

        if start_timestamp > start_date:
            logger.info(
                (
                    "Not enough predictions data in the lake. "
                    "Make sure you fetch data starting from %s up to today"
                ),
                time.strftime("%Y-%m-%d", time.localtime(start_date)),
            )
            return False

        return True
