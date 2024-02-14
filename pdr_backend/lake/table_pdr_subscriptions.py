from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Int64, Utf8, Float32

from pdr_backend.subgraph.subgraph_subscriptions import (
    fetch_filtered_subscriptions,
)
from pdr_backend.lake.plutil import save_df_to_parquet
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.plutil import _object_list_to_df
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
    network: str,
    st_ut: int,
    fin_ut: int,
    save_backoff_limit: int,
    pagination_limit: int,
    config: Dict,
    filename: str,
):
    """
    @description
        Fetch raw subscription events from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch subscriptions
    save_backoff_count = 0
    pagination_offset = 0

    final_df = pl.DataFrame()
    while True:
        # call the function
        subscriptions = fetch_filtered_subscriptions(
            ms_to_seconds(st_ut),
            ms_to_seconds(fin_ut),
            pagination_limit,
            pagination_offset,
            config["contract_list"],
            network,
        )
        # convert subscriptions to df and transform timestamp into ms
        subscription_df = _object_list_to_df(subscriptions, subscriptions_schema)
        subscription_df = _transform_timestamp_to_ms(subscription_df)
        subscription_df = subscription_df.filter(
            pl.col("timestamp").is_between(st_ut, fin_ut)
        ).sort("timestamp")

        if len(final_df) == 0:
            final_df = subscription_df
        else:
            final_df = pl.concat([final_df, subscription_df])

        save_backoff_count += len(subscription_df)

        # save to file if requred number of data has been fetched
        if (
            save_backoff_count > save_backoff_limit
            or len(subscription_df) < pagination_limit
        ) and len(final_df) > 0:
            assert subscription_df.schema == subscriptions_schema
            # save to parquet
            save_df_to_parquet(filename, final_df)
            final_df = pl.DataFrame()
            save_backoff_count = 0

        # avoids doing next fetch if we've reached the end
        if len(subscription_df) < pagination_limit:
            break
        pagination_offset += pagination_limit
