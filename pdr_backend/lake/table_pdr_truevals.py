from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Int64, Utf8


from pdr_backend.subgraph.subgraph_trueval import fetch_truevals
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

# RAW TRUEVAL SCHEMA
truevals_schema = {
    "ID": Utf8,
    "token": Utf8,
    "timestamp": Int64,
    "trueValue": Boolean,
    "slot": Int64,
}


@enforce_types
def get_pdr_truevals_df(
    network: str, st_ut: int, fin_ut: int, config: Dict
) -> pl.DataFrame:
    """
    @description
        Fetch raw truevals from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch truevals
    truevals = fetch_truevals(
        config["contract_list"], ms_to_seconds(st_ut), ms_to_seconds(fin_ut), 0, network
    )

    if len(truevals) == 0:
        print("      No truevals to fetch. Exit.")
        return pl.DataFrame()

    # convert truevals to df and transform timestamp into ms
    trueval_df = _object_list_to_df(truevals, truevals_schema)

    return trueval_df
