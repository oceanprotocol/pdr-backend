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
from pdr_backend.lake.table_pdr_predictions import _transform_timestamp_to_ms


bronze_pdr_predictions_table_name = "bronze_pdr_predictions"

# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
bronze_pdr_predictions_schema = {
    "ID": Utf8,  # f"{contract}-{slot}-{user}"
    "contract": Utf8,  # f"{contract}"
    "slot_id": Utf8,  # f"{contract}-{slot}"
    "pair": Utf8,
    "timeframe": Utf8,
    "predvalue": Boolean,
    "stake": Float64,
    "truevalue": Boolean,
    "timestamp": Int64,
    "last_event_timestamp": Int64,
    "source": Utf8,
    "payout": Float64,
    "revenue": Float64,
    "slot": Int64,
    "user": Utf8,
}


def _process_predictions(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    @description
        Perform post-fetch processing on the data.
        1. Find predictions within the update
        2. Transform predictions to bronze
        3. Concat to existing table
    """
    predictions_df, _ = pick_df_and_ids_on_period(
        target=dfs["pdr_predictions"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    def get_slot_id(_id: str) -> str:
        slot_id = _id.split("-")[0] + "-" + _id.split("-")[1]
        return f"{slot_id}"

    # transform from raw to bronze_prediction
    bronze_predictions_df = predictions_df.with_columns(
        [
            pl.col("ID").map_elements(get_slot_id, return_dtype=Utf8).alias("slot_id"),
            pl.col("prediction").alias("predvalue"),
            pl.col("trueval").alias("truevalue"),
            pl.lit(None).alias("revenue"),
            pl.col("timestamp").alias("timestamp"),
            pl.col("timestamp").alias("last_event_timestamp"),
        ]
    ).select(bronze_pdr_predictions_schema)

    print(">>>> _process_predictions bronze_predictions_df:", bronze_predictions_df)

    # Append new predictions
    # Upsert existing predictions
    cur_bronze = dfs[bronze_pdr_predictions_table_name]
    df = pl.concat([cur_bronze, bronze_predictions_df])
    df = df.filter(pl.struct("ID").is_unique())
    dfs[bronze_pdr_predictions_table_name] = df
    return dfs


def _process_payouts(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    @description
        Perform post-fetch processing on the data
        1. Find payouts within the update

    """
    payouts_df, payouts_ids = pick_df_and_ids_on_period(
        target=dfs["pdr_payouts"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    print(">>>>_process_payouts payouts_df:", payouts_df)

    predictions_df = filter_and_drop_columns(
        df=dfs[bronze_pdr_predictions_table_name],
        target_column="ID",
        ids=payouts_ids,
        columns_to_drop=["payout", "predvalue"],
    )

    print(">>>>_process_payouts predictions_df filter:", predictions_df)

    predictions_df = left_join_with(
        target=predictions_df,
        other=payouts_df,
        w_columns=[
            pl.col("predictedValue").alias("predvalue"),
            pl.col("timestamp").alias("last_event_timestamp"),
        ],
        select_columns=bronze_pdr_predictions_schema.keys(),
    )

    print(">>>>_process_payouts predictions_df left_join:", predictions_df)
    print(">>> columns:", predictions_df.columns)
    print(">>> timestamp:", predictions_df["timestamp"])
    print(">>> last_event_timestamp:", predictions_df["last_event_timestamp"])

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
        target_column="slot_id",
        ids=truevals_ids,
        columns_to_drop=["truevalue"],
    )

    predictions_df = left_join_with(
        target=predictions_df,
        other=truevals_df,
        left_on="slot_id",
        right_on="ID",
        w_columns=[
            pl.col("truevalue").alias("truevalue"),
            pl.col("timestamp").alias("last_event_timestamp"),
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
    # gql_dfs = _process_truevals(gql_dfs, ppss)

    # # cull any records outside of our time range and sort them by timestamp
    # df = df.filter(
    #     pl.col("timestamp").is_between(
    #         ppss.lake_ss.st_timestamp, ppss.lake_ss.fin_timestamp
    #     )
    # ).sort("timestamp")

    return gql_dfs[bronze_pdr_predictions_table_name]
