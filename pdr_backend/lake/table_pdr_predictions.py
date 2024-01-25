from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.subgraph.subgraph_predictions import (
    FilterMode,
    fetch_filtered_predictions,
)
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

# RAW PREDICTOOR PREDICTIONS SCHEMA
predictions_schema = {
    "ID": Utf8,
    "contract": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "prediction": Boolean,
    "stake": Float64,
    "trueval": Boolean,
    "timestamp": Int64,
    "source": Utf8,
    "payout": Float64,
    "slot": Int64,
    "user": Utf8,
}

# PREDICTOOR_SUMMARY_SCHEMA
predictoor_summary_df_schema = {
    "timeframe": Utf8,
    "pair": Utf8,
    "source": Utf8,
    "accuracy": Float64,
    "sum_stake": Float64,
    "sum_payout": Float64,
    "n_predictions": Int64,
    "user": Utf8,
}

# FEED_SUMMARY_SCHEMA
feed_summary_df_schema = {
    "timeframe": Utf8,
    "pair": Utf8,
    "source": Utf8,
    "accuracy": Float64,
    "sum_stake": Float64,
    "sum_payout": Float64,
    "n_predictions": Int64,
}


def _transform_timestamp_to_ms(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp"),
        ]
    )
    return df


@enforce_types
def get_pdr_predictions_df(
    network: str, st_ut: int, fin_ut: int, config: Dict
) -> pl.DataFrame:
    """
    @description
        Fetch raw predictions from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch predictions
    predictions = fetch_filtered_predictions(
        ms_to_seconds(st_ut),
        ms_to_seconds(fin_ut),
        config["contract_list"],
        network,
        FilterMode.CONTRACT_TS,
        payout_only=False,
        trueval_only=False,
    )

    if len(predictions) == 0:
        print("      No predictions to fetch. Exit.")
        return pl.DataFrame()

    # convert predictions to df and transform timestamp into ms
    predictions_df = _object_list_to_df(predictions, predictions_schema)
    predictions_df = _transform_timestamp_to_ms(predictions_df)

    # cull any records outside of our time range and sort them by timestamp
    predictions_df = predictions_df.filter(
        pl.col("timestamp").is_between(st_ut, fin_ut)
    ).sort("timestamp")

    return predictions_df
