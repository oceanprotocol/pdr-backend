import logging
from typing import Callable, Dict
from enforce_typing import enforce_types
import polars as pl
from pdr_backend.lake.table import Table
from pdr_backend.util.timeutil import current_ut_ms, pretty_timestr
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

    def get_gql_tables(self) -> Dict[str, Table]:
        """
        @description
          Get historical dataframes across many feeds and timeframes.

        @return
          predictions_df -- *polars* Dataframe. See class docstring
        """

        logger.info("Get predictions data across many feeds and timeframes.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut

        print(f"  Data start: {pretty_timestr(self.ppss.lake_ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(self.ppss.lake_ss.st_timestamp)}")

        self._update()

        logger.info("Get historical data across many subgraphs. Done.")

        # postconditions
        for _, table in self.record_config["tables"].items():
            assert isinstance(table.df, pl.DataFrame)

        return self.record_config["tables"]

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
            filename = table._parquet_filename()
            st_ut = table._calc_start_ut(filename)
            fin_ut = self.ppss.lake_ss.fin_timestamp
            print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
            if st_ut > min(current_ut_ms(), fin_ut):
                print("      Given start time, no data to gather. Exit.")

            # to satisfy mypy, get an explicit function pointer
            do_fetch: Callable[[str, int, int, int, int, Dict, str], pl.DataFrame] = (
                table.get_pdr_df
            )

            # number of data at which we want to save to file
            save_backoff_limit = 5000
            # number of data fetched from the subgraph at a time
            pagination_limit = 1000

            print(f"Updating table {table.table_name}")
            do_fetch(
                self.record_config["fetch_functions"][table.table_name],
                self.ppss.web3_pp.network,
                st_ut,
                fin_ut,
                save_backoff_limit,
                pagination_limit,
                self.record_config["config"],
            )
            table.load()
