from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.plutil import (
    pick_df_and_ids_on_period,
)
from pdr_backend.ppss.ppss import PPSS


bronze_pdr_slots_table_name = "bronze_pdr_slots"

# CLEAN & ENRICHED PREDICTOOR SLOTS SCHEMA
bronze_pdr_slots_schema = {
    "ID": Utf8,  # f"{contract}-{slot}"
    "contract": Utf8,  # f"{contract}"
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "slot": Int64,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
    "trueval": Boolean,
    "timestamp": Int64,
    "last_event_timestamp": Int64,
}


def _process_slots(
    collision_ids: pl.Series, dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    @description
        Perform post-fetch processing on the data.
        1. Find slots within the update
        2. Transform slots to bronze
        3. Concat to existing table
    """

    # only add new slots
    slots_df = dfs["pdr_slots"].filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        & (pl.col("ID").is_in(collision_ids).not_())
    )

    # select only the columns that we need
    columns_to_select = [
        "ID",
        "slot",
        "timestamp",
        "roundSumStakesUp",
        "roundSumStakes",
    ]
    slots_df = slots_df.select(columns_to_select)

    # create contract column from the ID column
    slots_df = slots_df.with_columns(
        contract=pl.col("ID").map_elements(lambda s: s.split("-")[0])
    )

    if len(slots_df) == 0:
        return dfs

    # append to existing dataframe
    new_bronze_df = pl.concat([dfs[bronze_pdr_slots_table_name], slots_df])
    dfs[bronze_pdr_slots_table_name] = new_bronze_df
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

    # get ref to bronze_slots
    slots_df = dfs[bronze_pdr_slots_table_name]

    # add columns that are going to be populated
    slots_df = slots_df.with_columns(last_event_timestamp=pl.lit(None))
    slots_df = slots_df.with_columns(trueval=pl.lit(None))

    initial_schema_keys = slots_df.schema.keys()

    # update only the ones within this time range
    slots_df = (
        slots_df.join(truevals_df, left_on="ID", right_on="ID", how="left")
        .with_columns(
            [
                pl.col("trueval").fill_null(pl.col("trueval")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["trueval", "last_event_timestamp"])
        .rename(
            {
                "trueval_right": "trueval",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(initial_schema_keys)
    )

    # update dfs
    dfs[bronze_pdr_slots_table_name] = slots_df
    return dfs


def _process_predictions(
    dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> Dict[str, pl.DataFrame]:
    """
    @description
        Perform post-fetch processing on the data
        1. Find predictions( within the update

    """
    # get predictions within the update
    predictions_df, _ = pick_df_and_ids_on_period(
        target=dfs["pdr_predictions"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get existing bronze_predictions we'll be updating
    slots_df = dfs[bronze_pdr_slots_table_name]

    # add columns that are going to be populated
    slots_df = slots_df.with_columns(pair=pl.lit(None))
    slots_df = slots_df.with_columns(source=pl.lit(None))
    slots_df = slots_df.with_columns(timeframe=pl.lit(None))

    initial_schema_keys = slots_df.schema.keys()

    # do work to join from pdr_payout onto bronze_pdr_predictions
    slots_df = (
        slots_df.join(predictions_df, on=["contract"], how="left")
        .with_columns(
            [
                pl.col("pair").fill_null(pl.col("pair")),
                pl.col("source").fill_null(pl.col("source")),
                pl.col("timeframe").fill_null(pl.col("timeframe")),
            ]
        )
        .drop(["pair", "source", "timeframe"])
        .rename(
            {
                "pair_right": "pair",
                "source_right": "source",
                "timeframe_right": "timeframe",
            }
        )
        .select(initial_schema_keys)
    )

    slots_df = slots_df.unique(subset=["ID"])

    print(slots_df)
    print(slots_df.columns)

    # update dfs
    dfs[bronze_pdr_slots_table_name] = slots_df
    return dfs


@enforce_types
def get_bronze_pdr_predictions_df(
    gql_dfs: Dict[str, pl.DataFrame], ppss: PPSS
) -> pl.DataFrame:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """

    # retrieve pred ids that are already in the lake
    collision_ids = gql_dfs[bronze_pdr_slots_table_name].filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
    )["ID"]

    # do post sync processing
    gql_dfs = _process_slots(collision_ids, gql_dfs, ppss)
    gql_dfs = _process_predictions(gql_dfs, ppss)
    gql_dfs = _process_truevals(gql_dfs, ppss)

    # after all post processing, return bronze_predictions
    df = gql_dfs[bronze_pdr_slots_table_name]
    return df
