#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Dict, Type

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.table import NamedTable, TempTable
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.trueval import Trueval
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_predictions import get_all_contract_ids_by_owner
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("gql_data_factory")


# Registered GQL fetches & tables
_GQLDF_REGISTERED_LAKE_TABLES = [
    Prediction,
    Trueval,
    Payout,
]

_GQLDF_REGISTERED_TABLE_NAMES = [
    t.get_lake_table_name() for t in _GQLDF_REGISTERED_LAKE_TABLES  # type: ignore[attr-defined]
]


@enforce_types
class GQLDataFactory:
    """
    Roles:
    - From each GQL API, fill >=1 gql_dfs -> parquet files data lake
    - From gql_dfs, calculate other dfs and stats
    - All timestamps, after fetching, are transformed into milliseconds wherever appropriate

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, ppss: PPSS):
        self.ppss = ppss

        # filter by feed contract address
        network = get_sapphire_postfix(ppss.web3_pp.network)
        contract_list = get_all_contract_ids_by_owner(
            owner_address=self.ppss.web3_pp.owner_addrs,
            network=network,
        )

        contract_list = [f.lower() for f in contract_list]

        # configure all DB tables <> QGL queries
        self.record_config = {
            "config": {
                "contract_list": contract_list,
            }
        }

    def _prepare_temp_table(self, dataclass: Type[LakeMapper], st_ut, fin_ut):
        """
        @description
            _prepare_temp_table is a helper function to fill the temp table with
            missing data that already exists in the csv files. This way all new records
            can be appended to the temp table and then moved to the live table.

            # 1. get last timestamp from database
            # 2. get last timestamp from csv
            # 3. in preparation to append, check missing data to move FROM CSV -> TO TEMP TABLES
            # 4. resume appending to CSVs + Temp tables until complete
        """
        table = NamedTable.from_dataclass(dataclass)
        temp_table = TempTable.from_dataclass(dataclass)
        schema = dataclass.get_lake_schema()
        csv_last_timestamp = CSVDataStore.from_table(
            table, self.ppss
        ).get_last_timestamp()
        db_last_timestamp = DuckDBDataStore(self.ppss.lake_ss.lake_dir).query_data(
            f"SELECT MAX(timestamp) FROM {table.fullname}"
        )

        if csv_last_timestamp is None:
            return

        if (db_last_timestamp is None) or (
            db_last_timestamp['max("timestamp")'][0] is None
        ):
            logger.info(
                "  Table not yet created. Insert all %s csv data", table.fullname
            )
            data = CSVDataStore.from_table(table, self.ppss).read_all(schema)
            temp_table._append_to_db(data, self.ppss)
            return

        if db_last_timestamp['max("timestamp")'][0] and (
            csv_last_timestamp > db_last_timestamp['max("timestamp")'][0]
        ):
            logger.info("  Table exists. Insert pending %s csv data", table.fullname)
            data = CSVDataStore.from_table(table, self.ppss).read(
                st_ut,
                fin_ut,
                schema,
            )
            temp_table._append_to_db(data, self.ppss)

    @enforce_types
    def _calc_start_ut(self, table: NamedTable) -> UnixTimeMs:
        """
        @description
            Calculate start timestamp, reconciling whether file exists and where
            its data starts. If file exists, you can only append to end.

        @arguments
            table -- Table object

        @return
            start_ut - timestamp (ut) to start grabbing data for (in ms)
        """

        last_timestamp = CSVDataStore.from_table(table, self.ppss).get_last_timestamp()

        start_ut = (
            last_timestamp
            if last_timestamp is not None
            else self.ppss.lake_ss.st_timestamp
        )

        return UnixTimeMs(start_ut + 1000)

    @enforce_types
    def _do_subgraph_fetch(
        self,
        dataclass: Type[LakeMapper],
        network: str,
        st_ut: UnixTimeMs,
        fin_ut: UnixTimeMs,
        config: Dict,
        save_backoff_limit: int = 5000,
        pagination_limit: int = 1000,
    ):
        """
        @description
            Fetch raw data from predictoor subgraph
            Update function for graphql query, returns raw data
            + Transforms ts into ms as required for data factory
        """
        table = NamedTable.from_dataclass(dataclass)
        temp_table = TempTable.from_dataclass(dataclass)

        logger.info("Fetching data for %s", table.fullname)
        network = get_sapphire_postfix(network)

        # save to file when this amount of data is fetched
        save_backoff_count = 0
        pagination_offset = 0

        buffer_df = pl.DataFrame([], schema=dataclass.get_lake_schema())

        DuckDBDataStore(self.ppss.lake_ss.lake_dir).create_table_if_not_exists(
            temp_table.fullname,
            dataclass.get_lake_schema(),
        )

        while True:
            # call the function
            fetch_function = dataclass.get_fetch_function()
            data = fetch_function(
                st_ut.to_seconds(),
                fin_ut.to_seconds(),
                config["contract_list"],
                pagination_limit,
                pagination_offset,
                network,
            )

            logger.info("Fetched %s from subgraph", len(data))
            # convert predictions to df and transform timestamp into ms
            df = _object_list_to_df(
                data,
                fallback_schema=dataclass.get_lake_schema(),
            )
            df = _transform_timestamp_to_ms(df)
            df = df.filter(pl.col("timestamp").is_between(st_ut, fin_ut))

            if len(df) > 0:
                if df["timestamp"][0] > df["timestamp"][len(df) - 1]:
                    df = df.filter(pl.col("timestamp") >= df["timestamp"][0])

            if len(buffer_df) == 0:
                buffer_df = df
            else:
                buffer_df = buffer_df.vstack(df)

            save_backoff_count += len(df)

            # save to file if required number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(buffer_df) > 0:
                assert df.schema == dataclass.get_lake_schema()
                temp_table.append_to_storage(buffer_df, self.ppss)
                logger.info(
                    "Saved %s records to storage while fetching", len(buffer_df)
                )

                buffer_df = pl.DataFrame(
                    [],
                    schema=dataclass.get_lake_schema(),
                )
                save_backoff_count = 0
                if df["timestamp"][0] > df["timestamp"][len(df) - 1]:
                    return

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

        if len(buffer_df) > 0:
            temp_table.append_to_storage(buffer_df, self.ppss)
            logger.info("Saved %s records to storage while fetching", len(buffer_df))

    @enforce_types
    def _move_from_temp_tables_to_live(self):
        """
        @description
            Move the records from our ETL temporary build tables to live, in-production tables
        """

        db = DuckDBDataStore(self.ppss.lake_ss.lake_dir)
        for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
            temp_table = TempTable.from_dataclass(dataclass)

            db.move_table_data(temp_table, NamedTable.from_dataclass(dataclass))
            db.drop_table(temp_table.fullname)

    @enforce_types
    def _update(self):
        """
        @description
            Iterate across all gql queries and update their lake data:
            - Predictoors
            - Claims

            Improve this by:
            1. Break out raw data from any transformed/cleaned data
            2. Integrate other queries and summaries
            3. Integrate config/pp if needed
        @arguments
            fin_ut -- a timestamp, in ms, in UTC
        """
        logger.info("  Data start: %s", self.ppss.lake_ss.st_timestamp.pretty_timestr())
        logger.info("  Data fin: %s", self.ppss.lake_ss.fin_timestamp.pretty_timestr())

        fin_ut = self.ppss.lake_ss.fin_timestamp

        for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
            # calculate start and end timestamps
            table = NamedTable.from_dataclass(dataclass)
            st_ut = self._calc_start_ut(table)
            logger.info(
                "      Aim to fetch data from start_time: [%s] to end_time: [%s]",
                st_ut.pretty_timestr(),
                fin_ut.pretty_timestr(),
            )
            if st_ut > min(UnixTimeMs.now(), fin_ut):
                logger.info("      Given start time, no data to gather. Exit.")

            # make sure that unwritten csv records are pre-loaded into the temp table
            self._prepare_temp_table(dataclass, st_ut, fin_ut)

            # fetch from subgraph and add to temp table
            logger.info("Updating table %s", table.fullname)
            self._do_subgraph_fetch(
                dataclass,
                self.ppss.web3_pp.network,
                st_ut,
                fin_ut,
                self.record_config["config"],
            )

        # move data from temp tables to live tables
        self._move_from_temp_tables_to_live()
        logger.info("GQLDataFactory - Update done.")
