import logging
from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Int64, Utf8


from pdr_backend.subgraph.subgraph_trueval import fetch_truevals
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

truevals_table_name = "pdr_truevals"
logger = logging.getLogger("lake_pdr_truevals")

# RAW TRUEVAL SCHEMA
truevals_schema = {
    "ID": Utf8,
    "token": Utf8,
    "timestamp": Int64,
    "trueval": Boolean,
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
        ms_to_seconds(st_ut), ms_to_seconds(fin_ut), config["contract_list"], network
    )

    if len(truevals) == 0:
        logger.warning("No truevals to fetch. Exit.")
        return pl.DataFrame()

    # convert truevals to df, transform timestamp into ms, return in-order
    trueval_df = _object_list_to_df(truevals, truevals_schema)
    trueval_df = _transform_timestamp_to_ms(trueval_df)
    trueval_df = trueval_df.sort("timestamp")

    return trueval_df
