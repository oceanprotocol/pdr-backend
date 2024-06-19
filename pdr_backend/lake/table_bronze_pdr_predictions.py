from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8
from pdr_backend.lake.plutil import (
    pick_df_and_ids_on_period,
)
from pdr_backend.lake.legacy.table import Table
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
    collision_ids: pl.Series, tables: Dict[str, Table], ppss: PPSS
) -> Dict[str, Table]:
    """
    @description
        Perform post-fetch processing on the data.
        1. Find predictions within the update
        2. Transform predictions to bronze
        3. Concat to existing table
    """
    # only add new predictions
    predictions_df = tables["pdr_predictions"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        & (pl.col("ID").is_in(collision_ids).not_())
    )

    if len(predictions_df) == 0:
        return tables

    # transform from raw to bronze_prediction
    def get_slot_id(_id: str) -> str:
        slot_id = _id.split("-")[0] + "-" + _id.split("-")[1]
        return f"{slot_id}"

    bronze_predictions_df = predictions_df.with_columns(
        [
            pl.col("ID").map_elements(get_slot_id, return_dtype=Utf8).alias("slot_id"),
            pl.col("predvalue").alias("predvalue"),
            pl.col("truevalue").alias("truevalue"),
            pl.col("timestamp").alias("timestamp"),
            pl.col("timestamp").alias("last_event_timestamp"),
        ]
    ).select(bronze_pdr_predictions_schema)

    # append to existing dataframe
    new_bronze_df = pl.concat(
        [tables[bronze_pdr_predictions_table_name].df, bronze_predictions_df]
    )
    tables[bronze_pdr_predictions_table_name].df = new_bronze_df
    return tables


def _process_truevals(tables: Dict[str, Table], ppss: PPSS) -> Dict[str, Table]:
    """
    Perform post-fetch processing on the data
    """
    # get truevals within the update
    truevals_df, _ = pick_df_and_ids_on_period(
        target=tables["pdr_truevals"].df,
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get ref to bronze_predictions
    predictions_df = tables[bronze_pdr_predictions_table_name].df

    # update only the ones within this time range
    predictions_df = (
        predictions_df.join(
            truevals_df, left_on="slot_id", right_on="ID", how="left", coalesce=True
        )
        .with_columns(
            [
                pl.col("truevalue_right").fill_null(pl.col("truevalue")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["truevalue", "last_event_timestamp"])
        .rename(
            {
                "truevalue_right": "truevalue",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(bronze_pdr_predictions_schema.keys())
    )

    # update dfs
    tables[bronze_pdr_predictions_table_name].df = predictions_df
    return tables


def _process_payouts(tables: Dict[str, Table], ppss: PPSS) -> Dict[str, Table]:
    """
    @description
        Perform post-fetch processing on the data
        1. Find payouts within the update

    """
    # get payouts within the update
    payouts_df, _ = pick_df_and_ids_on_period(
        target=tables["pdr_payouts"].df,
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get existing bronze_predictions we'll be updating
    predictions_df = tables[bronze_pdr_predictions_table_name].df

    # do work to join from pdr_payout onto bronze_pdr_predictions
    predictions_df = (
        predictions_df.join(payouts_df, on=["ID"], how="left", coalesce=True)
        .with_columns(
            [
                pl.col("payout_right").fill_null(pl.col("payout")),
                pl.col("predvalue_right").fill_null(pl.col("predvalue")),
                pl.col("stake_right").fill_null(pl.col("stake")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["payout", "predvalue", "stake", "last_event_timestamp"])
        .rename(
            {
                "payout_right": "payout",
                "predvalue_right": "predvalue",
                "stake_right": "stake",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(bronze_pdr_predictions_schema.keys())
    )

    # update dfs
    tables[bronze_pdr_predictions_table_name].df = predictions_df
    return tables


@enforce_types
def get_bronze_pdr_predictions_table(gql_tables: Dict[str, Table], ppss: PPSS) -> Table:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """

    collision_ids: pl.Series = pl.Series([])
    # retrieve pred ids that are already in the lake
    if len(gql_tables[bronze_pdr_predictions_table_name].df) > 0:
        collision_ids = gql_tables[bronze_pdr_predictions_table_name].df.filter(
            (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
            & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        )["ID"]

    # do post sync processing
    gql_tables = _process_predictions(collision_ids, gql_tables, ppss)
    gql_tables = _process_truevals(gql_tables, ppss)
    gql_tables = _process_payouts(gql_tables, ppss)

    # after all post processing, return bronze_predictions
    return gql_tables[bronze_pdr_predictions_table_name]
