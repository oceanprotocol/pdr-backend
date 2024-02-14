from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Int64, Utf8

from pdr_backend.lake.plutil import save_df_to_parquet
from pdr_backend.subgraph.subgraph_trueval import fetch_truevals
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

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
        Fetch raw truevals from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch truevals
    save_backoff_count = 0
    pagination_offset = 0

    final_df = pl.DataFrame()
    while True:
        # call the function
        truevals = fetch_truevals(
            ms_to_seconds(st_ut),
            ms_to_seconds(fin_ut),
            pagination_limit,
            pagination_offset,
            config["contract_list"],
            network,
        )
        # convert truevals to df and transform timestamp into ms
        trueval_df = _object_list_to_df(truevals, truevals_schema)
        trueval_df = _transform_timestamp_to_ms(trueval_df)

        if len(final_df) == 0:
            final_df = trueval_df
        else:
            final_df = pl.concat([final_df, trueval_df])

        save_backoff_count += len(trueval_df)

        # save to file if requred number of data has been fetched
        if (
            save_backoff_count > save_backoff_limit
            or len(trueval_df) < pagination_limit
        ) and len(final_df) > 0:
            assert trueval_df.schema == truevals_schema
            trueval_df = trueval_df.filter(
                pl.col("timestamp").is_between(st_ut, fin_ut)
            ).sort("timestamp")
            # save to parquet
            save_df_to_parquet(filename, final_df)
            final_df = pl.DataFrame()
            save_backoff_count = 0

        # avoids doing next fetch if we've reached the end
        if len(trueval_df) < pagination_limit:
            break
        pagination_offset += pagination_limit
