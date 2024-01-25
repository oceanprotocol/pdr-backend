from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.plutil import (
    left_join_with,
    filter_and_drop_columns,
    pick_df_and_ids_on_period,
)
from pdr_backend.ppss.ppss import PPSS


bronze_pdr_predictions_table_name = "bronze_pdr_predictions"

# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
bronze_pdr_predictions_schema = {
    "ID": Utf8,
    "truevalue_id": Utf8,
    "contract": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "predvalue": Boolean,
    "stake": Float64,
    "truevalue": Boolean,
    "timestamp": Int64,
    "source": Utf8,
    "payout": Float64,
    "revenue": Float64,
    "slot": Int64,
    "user": Utf8,
}


def _transform_timestamp_to_ms(df: pl.DataFrame) -> pl.DataFrame:
    df = df.with_columns(
        [
            pl.col("timestamp").mul(1000).alias("timestamp"),
        ]
    )
    return df


def _process_predictions(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    Perform post-fetch processing on the data
    """
    predictions_df = pl.DataFrame()

    dfs[bronze_pdr_predictions_table_name] = predictions_df
    return dfs


def _process_payouts(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    Perform post-fetch processing on the data
    """
    payouts_df, payouts_ids = pick_df_and_ids_on_period(
        target=dfs["pdr_payouts"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    predictions_df = filter_and_drop_columns(
        df=dfs[bronze_pdr_predictions_table_name],
        target_column="ID",
        ids=payouts_ids,
        columns_to_drop=["payout", "prediction"],
    )

    predictions_df = left_join_with(
        target=predictions_df,
        other=payouts_df,
        w_columns=[
            pl.col("predvalue").alias("prediction"),
        ],
        select_columns=bronze_pdr_predictions_schema.keys(),
    )

    dfs[bronze_pdr_predictions_table_name] = predictions_df
    return dfs


def _process_truevals(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    Perform post-fetch processing on the data
    """
    truevals_df, truevals_ids = pick_df_and_ids_on_period(
        target=dfs["pdr_truevals"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    predictions_df = filter_and_drop_columns(
        df=dfs[bronze_pdr_predictions_table_name],
        target_column="truevalue_id",
        ids=truevals_ids,
        columns_to_drop=["truevalue"],
    )

    predictions_df = left_join_with(
        target=predictions_df,
        other=truevals_df,
        left_on="truevalue_id",
        right_on="ID",
        w_columns=[
            pl.col("truevalue").alias("truevalue"),
        ],
        select_columns=bronze_pdr_predictions_schema.keys(),
    )

    dfs[bronze_pdr_predictions_table_name] = predictions_df
    return dfs


@enforce_types
def get_bronze_pdr_predictions_df(
    gql_dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> pl.DataFrame:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """
    # do post_sync processing
    gql_dfs = _process_predictions(gql_dfs, ppss)
    gql_dfs = _process_payouts(gql_dfs, ppss)
    gql_dfs = _process_truevals(gql_dfs, ppss)

    df = _transform_timestamp_to_ms(gql_dfs[bronze_pdr_predictions_table_name])

    # cull any records outside of our time range and sort them by timestamp
    df = df.filter(
        pl.col("timestamp").is_between(
            ppss.lake_ss.st_timestamp, ppss.lake_ss.fin_timestamp
        )
    ).sort("timestamp")

    return df
