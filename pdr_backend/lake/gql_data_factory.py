from typing import Dict
from enforce_typing import enforce_types
import polars as pl
from pdr_backend.util.timeutil import pretty_timestr

from pdr_backend.lake.table_pdr_predictions import (
    get_pdr_predictions_df,
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table_pdr_subscriptions import (
    get_pdr_subscriptions_df,
    subscriptions_schema,
    subscriptions_table_name,
)
from pdr_backend.lake.table_pdr_truevals import (
    get_pdr_truevals_df,
    truevals_schema,
    truevals_table_name,
)
from pdr_backend.lake.table_pdr_payouts import (
    get_pdr_payouts_df,
    payouts_schema,
    payouts_table_name,
)
from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_predictions import get_all_contract_ids_by_owner
from pdr_backend.util.networkutil import get_sapphire_postfix


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
                    get_pdr_predictions_df,
                    ppss,
                ),
                "pdr_subscriptions": Table(
                    subscriptions_table_name,
                    subscriptions_schema,
                    get_pdr_subscriptions_df,
                    ppss,
                ),
                "pdr_truevals": Table(
                    truevals_table_name, truevals_schema, get_pdr_truevals_df, ppss
                ),
                "pdr_payouts": Table(
                    payouts_table_name, payouts_schema, get_pdr_payouts_df, ppss
                ),
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
        print("Get predictions data across many feeds and timeframes.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut

        print(f"  Data start: {pretty_timestr(self.ppss.lake_ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(self.ppss.lake_ss.st_timestamp)}")

        self._update()
        self._load_parquet()

        print("Get historical data across many subgraphs. Done.")

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
            print(f"      Updating {table}")
            table.update(self.record_config["config"])

    def _load_parquet(self) -> Dict[str, Table]:
        """ """
        for _, table in self.record_config["tables"].items():
            print(f"  Loading parquet for {table}")
            table.load()
        return self.record_config["tables"]
