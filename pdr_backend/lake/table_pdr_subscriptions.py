from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Int64, Utf8, Float32

from pdr_backend.subgraph.subgraph_subscriptions import (
    fetch_filtered_subscriptions,
)
from pdr_backend.lake.plutil import (
    _object_list_to_df,
    _filter_and_sort_pdr_records
)
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds


# RAW PREDICTOOR SUBSCRIPTIONS SCHEMA
subscriptions_schema = {
    "ID": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "tx_id": Utf8,
    "last_price_value": Float32,
    "timestamp": Int64,
    "user": Utf8,
}


@enforce_types
def get_pdr_subscriptions_df(
    network: str, st_ut: int, fin_ut: int, config: Dict
) -> pl.DataFrame:
    """
    @description
        Fetch raw subscription events from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch subscriptions
    subscriptions = fetch_filtered_subscriptions(
        ms_to_seconds(st_ut), ms_to_seconds(fin_ut), config["contract_list"], network
    )

    if len(subscriptions) == 0:
        print("      No subscriptions fetched. Exit.")
        return pl.DataFrame()

    # convert subscriptions to df and transform timestamp into ms
    subscriptions_df = _object_list_to_df(subscriptions, subscriptions_schema)
    subscriptions_df = _filter_and_sort_pdr_records(subscriptions_df, st_ut, fin_ut)

    return subscriptions_df
