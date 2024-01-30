from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.plutil import (
    pick_df_and_ids_on_period,
)
from pdr_backend.ppss.ppss import PPSS


bronze_pdr_predictions_table_name = "bronze_pdr_predictions"

# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
bronze_pdr_predictions_schema = {
    "ID": Utf8,  # f"{contract}-{slot}-{user}"
    "slot_id": Utf8,  # f"{contract}-{slot}"
    "contract": Utf8,  # f"{contract}"
    "slot": Int64,
    "user": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "predvalue": Boolean,
    "truevalue": Boolean,
    "stake": Float64,
    "payout": Float64,
    "timestamp": Int64,
    "last_event_timestamp": Int64,
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
            pl.col("timestamp").alias("timestamp"),
            pl.col("timestamp").alias("last_event_timestamp"),
        ]
    ).select(bronze_pdr_predictions_schema)

    # Append new predictions
    # Upsert existing predictions
    cur_bronze = dfs[bronze_pdr_predictions_table_name]
    df = pl.concat([cur_bronze, bronze_predictions_df])
    df = df.filter(pl.struct("ID").is_unique())
    dfs[bronze_pdr_predictions_table_name] = df
    return dfs


def _process_truevals(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    Perform post-fetch processing on the data
    """
    # get truevals within the update
    truevals_df, _ = pick_df_and_ids_on_period(
        target=dfs["pdr_truevals"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get existing bronze_predictions we'll be updating
    predictions_df = dfs[bronze_pdr_predictions_table_name]

    # do work to join from pdr_truevals onto bronze_pdr_predictions
    predictions_df = (
        predictions_df.join(truevals_df, left_on="slot_id", right_on="ID", how="left")
        .with_columns(
            [
                pl.col("trueval").fill_null(pl.col("truevalue")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["truevalue", "last_event_timestamp"])
        .rename(
            {
                "trueval": "truevalue",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(bronze_pdr_predictions_schema.keys())
    )

    # update the predictions_df
    dfs[bronze_pdr_predictions_table_name] = predictions_df
    return dfs


def _process_payouts(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    @description
        Perform post-fetch processing on the data
        1. Find payouts within the update

    """
    # get payouts within the update
    payouts_df, _ = pick_df_and_ids_on_period(
        target=dfs["pdr_payouts"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get existing bronze_predictions we'll be updating
    predictions_df = dfs[bronze_pdr_predictions_table_name]

    # do work to join from pdr_payout onto bronze_pdr_predictions
    predictions_df = (
        predictions_df.join(payouts_df, on=["ID"], how="left")
        .with_columns(
            [
                pl.col("payout_right").fill_null(pl.col("payout")),
                pl.col("predictedValue").fill_null(pl.col("predvalue")),
                pl.col("stake_right").fill_null(pl.col("stake")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["payout", "predvalue", "stake", "last_event_timestamp"])
        .rename(
            {
                "payout_right": "payout",
                "predictedValue": "predvalue",
                "stake_right": "stake",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(bronze_pdr_predictions_schema.keys())
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
    gql_dfs = _process_truevals(gql_dfs, ppss)
    gql_dfs = _process_payouts(gql_dfs, ppss)

    df = gql_dfs[bronze_pdr_predictions_table_name]
    
    # cull any records outside of our time range and sort them by timestamp
    df = df.filter(
        pl.col("timestamp").is_between(
            ppss.lake_ss.st_timestamp, ppss.lake_ss.fin_timestamp
        )
    ).sort("timestamp")

    return df
