from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Int64, Float64, Utf8, Boolean

from pdr_backend.lake.plutil import save_df_to_parquet
from pdr_backend.subgraph.subgraph_payout import fetch_payouts
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms

# RAW PAYOUT SCHEMA
payouts_schema = {
    "ID": Utf8,
    "token": Utf8,
    "user": Utf8,
    "slot": Int64,
    "timestamp": Int64,
    "payout": Float64,
    "predictedValue": Boolean,
    "revenue": Float64,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
    "stake": Float64,
}


@enforce_types
def get_pdr_payouts_df(
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
        Fetch raw payouts from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # save to file when this amount of data is fetched
    save_backoff_count = 0
    pagination_offset = 0

    final_df = pl.DataFrame()
    while True:
        # call the function
        payouts = fetch_payouts(
            config["contract_list"],
            ms_to_seconds(st_ut),
            ms_to_seconds(fin_ut),
            pagination_limit,
            pagination_offset,
            network,
        )
        # convert payouts to df and transform timestamp into ms
        payout_df = _object_list_to_df(payouts, payouts_schema)
        payout_df = _transform_timestamp_to_ms(payout_df)
        payout_df = payout_df.filter(
            pl.col("timestamp").is_between(st_ut, fin_ut)
        ).sort("timestamp")

        if len(final_df) == 0:
            final_df = payout_df
        else:
            final_df = pl.concat([final_df, payout_df])

        save_backoff_count += len(payout_df)

        # save to file if requred number of data has been fetched
        if (
            save_backoff_count > save_backoff_limit or len(payout_df) < pagination_limit
        ) and len(final_df) > 0:
            assert payout_df.schema == payouts_schema
            # save to parquet
            save_df_to_parquet(filename, final_df)
            final_df = pl.DataFrame()
            save_backoff_count = 0

        # avoids doing next fetch if we've reached the end
        if len(payout_df) < pagination_limit:
            break
        pagination_offset += pagination_limit
