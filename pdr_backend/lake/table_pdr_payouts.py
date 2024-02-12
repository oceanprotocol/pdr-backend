from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Int64, Float64, Utf8, Boolean

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
    network: str, st_ut: int, fin_ut: int, first: int, skip: int, config: Dict
) -> pl.DataFrame:
    """
    @description
        Fetch raw payouts from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch payouts
    payouts = fetch_payouts(
        config["contract_list"],
        ms_to_seconds(st_ut),
        ms_to_seconds(fin_ut),
        first,
        skip,
        network,
    )

    if len(payouts) == 0:
        print("No payouts to fetch. Exit.")
        return pl.DataFrame()

    # convert payouts to df and transform timestamp into ms
    payout_df = _object_list_to_df(payouts, payouts_schema)
    payout_df = _transform_timestamp_to_ms(payout_df)

    # cull any records outside of our time range and sort them by timestamp
    payout_df = payout_df.filter(pl.col("timestamp").is_between(st_ut, fin_ut)).sort(
        "timestamp"
    )

    return payout_df
