import logging
from typing import Callable, Dict
from enforce_typing import enforce_types
import polars as pl
from pdr_backend.lake.table import Table
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
from pdr_backend.subgraph.subgraph_trueval import fetch_truevals
from pdr_backend.subgraph.subgraph_subscriptions import (
    fetch_filtered_subscriptions,
)
from pdr_backend.subgraph.subgraph_predictions import (
    fetch_filtered_predictions,
)
from pdr_backend.subgraph.subgraph_payout import fetch_payouts
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms

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
            "tables": {
                "pdr_predictions": Table(
                    predictions_table_name,
                    predictions_schema,
                    ppss,
                ),
                "pdr_subscriptions": Table(
                    subscriptions_table_name,
                    subscriptions_schema,
                    ppss,
                ),
                "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
                "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
            },
            "fetch_functions": {
                "pdr_predictions": fetch_filtered_predictions,
                "pdr_subscriptions": fetch_filtered_subscriptions,
                "pdr_truevals": fetch_truevals,
                "pdr_payouts": fetch_payouts,
            },
            "config": {
                "contract_list": contract_list,
            },
        }

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

        print(f"  Data start: {self.ppss.lake_ss.st_timestamp.pretty_timestr()}")
        print(f"  Data fin: {self.ppss.lake_ss.st_timestamp.pretty_timestr()}")

        self._update()

        logger.info("Get historical data across many subgraphs. Done.")

        # postconditions
        for _, table in self.record_config["tables"].items():
            assert isinstance(table.df, pl.DataFrame)

        return self.record_config["tables"]

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
        print(f"Fetching data for {table.table_name}")
        network = get_sapphire_postfix(network)

        # save to file when this amount of data is fetched
        save_backoff_count = 0
        pagination_offset = 0

        buffer_df = pl.DataFrame([], schema=table.df_schema)

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

            print(f"Fetched {len(data)} from subgraph")
            # convert predictions to df and transform timestamp into ms
            df = _object_list_to_df(data, table.df_schema)
            df = _transform_timestamp_to_ms(df)
            df = df.filter(pl.col("timestamp").is_between(st_ut, fin_ut)).sort(
                "timestamp"
            )

            if len(buffer_df) == 0:
                buffer_df = df
            else:
                buffer_df = buffer_df.vstack(df)

            save_backoff_count += len(df)

            # save to file if requred number of data has been fetched
            if (
                save_backoff_count >= save_backoff_limit or len(df) < pagination_limit
            ) and len(buffer_df) > 0:
                assert df.schema == table.df_schema
                table.append_to_storage(buffer_df)
                print(f"Saved {len(buffer_df)} records to file while fetching")

                buffer_df = pl.DataFrame([], schema=table.df_schema)
                save_backoff_count = 0

            # avoids doing next fetch if we've reached the end
            if len(df) < pagination_limit:
                break
            pagination_offset += pagination_limit

        if len(buffer_df) > 0:
            table.append_to_storage(buffer_df)
            print(f"Saved {len(buffer_df)} records to file while fetching")

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

        last_timestamp = table.csv_data_store.get_last_timestamp(table.table_name)

        start_ut = (
            last_timestamp
            if last_timestamp is not None
            else self.ppss.lake_ss.st_timestamp
        )

        return UnixTimeMs(start_ut + 1000)

    def _update(self):
        """
        @description
            Iterate across all gql queries and update their parquet files:
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

        for _, table in self.record_config["tables"].items():
            st_ut = self._calc_start_ut(table)
            fin_ut = self.ppss.lake_ss.fin_timestamp
            print(f"      Aim to fetch data from start time: {st_ut.pretty_timestr()}")
            if st_ut > min(UnixTimeMs.now(), fin_ut):
                print("      Given start time, no data to gather. Exit.")

            print(f"Updating table {table.table_name}")
            self._do_subgraph_fetch(
                table,
                self.record_config["fetch_functions"][table.table_name],
                self.ppss.web3_pp.network,
                st_ut,
                fin_ut,
                self.record_config["config"],
            )
