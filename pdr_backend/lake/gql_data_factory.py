import logging
from typing import Callable, Dict
from enforce_typing import enforce_types
import polars as pl
from pdr_backend.lake.table import Table, TableType, get_table_name, TempTable
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_predictions import get_all_contract_ids_by_owner
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table_pdr_subscriptions import (
    subscriptions_schema,
    subscriptions_table_name,
)
from pdr_backend.lake.table_pdr_truevals import (
    truevals_schema,
    truevals_table_name,
)
from pdr_backend.lake.table_pdr_payouts import (
    payouts_schema,
    payouts_table_name,
)
from pdr_backend.lake.table_pdr_slots import slots_table_name, slots_schema
from pdr_backend.subgraph.subgraph_trueval import fetch_truevals
from pdr_backend.subgraph.subgraph_subscriptions import (
    fetch_filtered_subscriptions,
)
from pdr_backend.subgraph.subgraph_predictions import (
    fetch_filtered_predictions,
)
from pdr_backend.subgraph.subgraph_payout import fetch_payouts
from pdr_backend.subgraph.subgraph_slot import fetch_slots
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.csv_data_store import CSVDataStore

logger = logging.getLogger("gql_data_factory")


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

        # configure all tables that will be recorded onto lake
        self.record_config = {
            "fetch_functions": {
                predictions_table_name: fetch_filtered_predictions,
                subscriptions_table_name: fetch_filtered_subscriptions,
                truevals_table_name: fetch_truevals,
                payouts_table_name: fetch_payouts,
                slots_table_name: fetch_slots,
            },
            "config": {
                "contract_list": contract_list,
            },
            "gql_tables": [
                predictions_table_name,
                subscriptions_table_name,
                truevals_table_name,
                payouts_table_name,
                slots_table_name,
            ],
        }

        TableRegistry().register_tables(
            {
                predictions_table_name: (
                    predictions_table_name,
                    predictions_schema,
                    self.ppss,
                ),
                subscriptions_table_name: (
                    subscriptions_table_name,
                    subscriptions_schema,
                    self.ppss,
                ),
                truevals_table_name: (truevals_table_name, truevals_schema, self.ppss),
                payouts_table_name: (payouts_table_name, payouts_schema, self.ppss),
                slots_table_name: (slots_table_name, slots_schema, self.ppss),
            }
        )

    @enforce_types
    def get_gql_tables(self) -> Dict[str, Table]:
        """
        @description
          Get historical dataframes across many feeds and timeframes.

        @return
          predictions_df -- *polars* Dataframe. See class docstring
        """

        logger.info("Get predictions data across many feeds and timeframes.")

        # st_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut

        logger.info("  Data start: %s", self.ppss.lake_ss.st_timestamp.pretty_timestr())
        logger.info("  Data fin: %s", self.ppss.lake_ss.st_timestamp.pretty_timestr())

        self._update()
        logger.info("Get historical data across many subgraphs. Done.")

        return TableRegistry().get_tables(self.record_config["gql_tables"])

    def _prepare_temp_table(self, table_name, st_ut, fin_ut, schema):
        """
        @description
            # 1. get last timestamp from database
            # 2. get last timestamp from csv
            # 3. check conditions and move to temp tables
        """
        table = TableRegistry().get_table(table_name)
        csv_last_timestamp = CSVDataStore(table.base_path).get_last_timestamp(
            table_name
        )
        db_last_timestamp = PersistentDataStore(table.base_path).query_data(
            f"SELECT MAX(timestamp) FROM {table_name}"
        )

        if csv_last_timestamp is None:
            return

        if db_last_timestamp is None:
            logger.info("  Table not yet created. Insert all %s csv data", table_name)
            data = CSVDataStore(table.base_path).read_all(table_name, schema)
            table._append_to_db(data, TableType.TEMP)
            return

        if csv_last_timestamp > db_last_timestamp['max("timestamp")'][0]:
            logger.info("  Table exists. Insert pending %s csv data", table_name)
            data = CSVDataStore(table.base_path).read(table_name, st_ut, fin_ut, schema)
            table._append_to_db(data, TableType.TEMP)

    @enforce_types
    def _calc_start_ut(self, table: Table) -> UnixTimeMs:
        """
        @description
            Calculate start timestamp, reconciling whether file exists and where
            its data starts. If file exists, you can only append to end.

        @arguments
            table -- Table object

        @return
            start_ut - timestamp (ut) to start grabbing data for (in ms)
        """

        last_timestamp = CSVDataStore(table.base_path).get_last_timestamp(
            table.table_name
        )

        start_ut = (
            last_timestamp
            if last_timestamp is not None
            else self.ppss.lake_ss.st_timestamp
        )

        return UnixTimeMs(start_ut + 1000)

    @enforce_types
    def _do_subgraph_fetch(
        self,
        table: Table,
        fetch_function: Callable,
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
        logger.info("Fetching data for %s", table.table_name)
        network = get_sapphire_postfix(network)

        # save to file when this amount of data is fetched
        save_backoff_count = 0
        pagination_offset = 0

        buffer_df = pl.DataFrame([], schema=table.df_schema)

        PersistentDataStore(self.ppss.lake_ss.lake_dir).create_table_if_not_exists(
            get_table_name(table.table_name, TableType.TEMP), table.df_schema
        )

        while True:
            # call the function
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
            df = _object_list_to_df(data, table.df_schema)
            df = _transform_timestamp_to_ms(df)
            df = df.filter(pl.col("timestamp").is_between(st_ut, fin_ut))

            if len(buffer_df) == 0:
                buffer_df = df
            else:
                buffer_df = buffer_df.vstack(df)

            save_backoff_count += len(df)

            # save to file if required number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(buffer_df) > 0:
                assert df.schema == table.df_schema
                table.append_to_storage(buffer_df, TableType.TEMP)
                logger.info(
                    "Saved %s records to storage while fetching", len(buffer_df)
                )

                buffer_df = pl.DataFrame([], schema=table.df_schema)
                save_backoff_count = 0
                if df["timestamp"][0] > df["timestamp"][len(df) - 1]:
                    return

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

        if len(buffer_df) > 0:
            table.append_to_storage(buffer_df, TableType.TEMP)
            logger.info("Saved %s records to storage while fetching", len(buffer_df))

    @enforce_types
    def _move_from_temp_tables_to_live(self):
        """
        @description
            Move the records from our ETL temporary build tables to live, in-production tables
        """

        pds = PersistentDataStore(self.ppss.lake_ss.lake_dir)
        for table_name in self.record_config["gql_tables"]:
            pds.move_table_data(
                TempTable(table_name),
                table_name,
            )

            pds.drop_table(get_table_name(table_name, TableType.TEMP))

    @enforce_types
    def _update(self):
        """
        @description
            Iterate across all gql queries and update their lake data:
            - Predictoors
            - Slots
            - Claims

            Improve this by:
            1. Break out raw data from any transformed/cleaned data
            2. Integrate other queries and summaries
            3. Integrate config/pp if needed
        @arguments
            fin_ut -- a timestamp, in ms, in UTC
        """

        for table in (
            TableRegistry().get_tables(self.record_config["gql_tables"]).values()
        ):
            # calculate start and end timestamps
            st_ut = self._calc_start_ut(table)
            fin_ut = self.ppss.lake_ss.fin_timestamp
            logger.info(
                "      Aim to fetch data from start time: %s", st_ut.pretty_timestr()
            )
            if st_ut > min(UnixTimeMs.now(), fin_ut):
                logger.info("      Given start time, no data to gather. Exit.")

            # make sure that unwritten csv records are pre-loaded into the temp table
            self._prepare_temp_table(table.table_name, st_ut, fin_ut, table.df_schema)

            # fetch from subgraph and add to temp table
            logger.info("Updating table %s", get_table_name(table.table_name))
            self._do_subgraph_fetch(
                table,
                self.record_config["fetch_functions"][table.table_name],
                self.ppss.web3_pp.network,
                st_ut,
                fin_ut,
                self.record_config["config"],
            )

        # move data from temp tables to live tables
        self._move_from_temp_tables_to_live()
        logger.info("GQLDataFactory - Update done.")
