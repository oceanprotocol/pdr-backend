from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.plutil import (
    pick_df_and_ids_on_period,
)
from pdr_backend.lake.table import Table
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
    collision_ids: pl.Series, tables: Dict[str, Table], ppss: PPSS
) -> Dict[str, Table]:
    """
    @description
        Perform post-fetch processing on the data.
        1. Find slots within the update
        2. Transform slots to bronze
        3. Concat to existing table
    """

    # only add new slots
    slots_df = tables["pdr_slots"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        & (pl.col("ID").is_in(collision_ids).not_())
    )

    if len(slots_df) == 0:
        return tables

    # get contract column
    def get_contract_id(_id: str) -> str:
        contract_id = _id.split("-")[0]
        return f"{contract_id}"

    # create bronze slots table in a strongly-defined manner
    bronze_slots_df = slots_df.with_columns(
        [
            pl.col("ID")
            .map_elements(get_contract_id, return_dtype=Utf8)
            .alias("contract"),
            pl.lit(None).alias("pair"),
            pl.lit(None).alias("timeframe"),
            pl.lit(None).alias("source"),
            pl.lit(None).alias("roundSumStakesUp"),
            pl.lit(None).alias("roundSumStakes"),
            pl.lit(None).alias("trueval"),
            pl.col("timestamp").alias("last_event_timestamp"),
        ]
    ).select(bronze_pdr_slots_schema)

    # append to existing dataframe
    new_bronze_df = pl.concat([tables[bronze_pdr_slots_table_name].df, bronze_slots_df])
    tables[bronze_pdr_slots_table_name].df = new_bronze_df
    return tables


def _process_truevals(tables: Dict[str, Table], ppss: PPSS) -> Dict[str, Table]:
    """
    @description
    Perform post-fetch processing on the data.
    1. Find truevals within the update
    2. Update slots with trueval values
    3. Update tables
    """

    # only add new truevals
    truevals_df = tables["pdr_truevals"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
    )

    if len(truevals_df) == 0:
        return tables

    # get ref to bronze_slots
    slots_df = tables[bronze_pdr_slots_table_name].df

    # filter out truevals that were already processed
    filtered_ids = slots_df.filter(slots_df["trueval"].is_not_null())["ID"].to_list()
    truevals_df = truevals_df.filter(~truevals_df["ID"].is_in(filtered_ids))

    # do work to join from pdr_truevals onto bronze_pdr_slots
    slots_df = (
        slots_df.join(truevals_df, on="ID", how="left")
        .with_columns(
            [
                pl.col("trueval_right").fill_null(pl.col("trueval")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["trueval", "last_event_timestamp"])
        .rename(
            {
                "timestamp_right": "last_event_timestamp",
                "trueval_right": "trueval",
            }
        )
        .select(bronze_pdr_slots_schema.keys())
    )
    # remove duplicate ids
    slots_df = slots_df.unique(subset=["ID"])

    # update dfs
    tables[bronze_pdr_slots_table_name].df = slots_df
    return tables


def _process_bronze_predictions(
    tables: Dict[str, Table], ppss: PPSS
) -> Dict[str, Table]:
    """
    @description
    1. Find prediction within the update
    2. Update slots with prediction values
    3. Update tables
    """
    # get predictions within the update
    bronze_predictions_df, _ = pick_df_and_ids_on_period(
        target=tables["bronze_pdr_predictions"].df,
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    # get existing bronze_predictions we'll be updating
    slots_df = tables[bronze_pdr_slots_table_name].df
    initial_schema_keys = slots_df.schema.keys()

    # do work to join from bronze_pdr_predictions onto bronze_pdr_slots
    slots_df = (
        slots_df.join(
            bronze_predictions_df, left_on="ID", right_on="slot_id", how="left"
        )
        .with_columns(
            [
                pl.col("pair").fill_null(pl.col("pair")),
                pl.col("source").fill_null(pl.col("source")),
                pl.col("timeframe").fill_null(pl.col("timeframe")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["pair", "source", "timeframe", "last_event_timestamp"])
        .rename(
            {
                "pair_right": "pair",
                "source_right": "source",
                "timeframe_right": "timeframe",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(initial_schema_keys)
    )
    slots_df = slots_df.unique(subset=["ID"])

    # update dfs
    tables[bronze_pdr_slots_table_name].df = slots_df.sort("timestamp")
    return tables


def _process_payouts(tables: Dict[str, Table], ppss: PPSS) -> Dict[str, Table]:
    """
    @description
    Perform post-fetch processing on the data
    1. Find payouts within the update
    2. Update slots with payout values
    3. Update tables
    """

    # get payouts within the update
    payouts_df = tables["pdr_payouts"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
    )
    payouts_df = payouts_df.sort("timestamp").reverse()

    def get_slot_id(_id: str) -> str:
        slot_id = _id.split("-")[0] + "-" + _id.split("-")[1]
        return f"{slot_id}"

    payouts_df = payouts_df.with_columns(
        [pl.col("ID").map_elements(get_slot_id, return_dtype=Utf8).alias("slot_id")]
    )

    # get existing bronze_predictions we'll be updating
    slots_df = tables[bronze_pdr_slots_table_name].df

    # do work to join from pdr_payouts onto bronze_pdr_slots
    slots_df = (
        slots_df.join(payouts_df, left_on="ID", right_on="slot_id", how="left")
        .with_columns(
            [
                pl.col("roundSumStakes_right").fill_null(pl.col("roundSumStakes")),
                pl.col("roundSumStakesUp_right").fill_null(pl.col("roundSumStakesUp")),
                pl.col("timestamp_right").fill_null(pl.col("last_event_timestamp")),
            ]
        )
        .drop(["roundSumStakes", "roundSumStakesUp", "last_event_timestamp"])
        .rename(
            {
                "roundSumStakes_right": "roundSumStakes",
                "roundSumStakesUp_right": "roundSumStakesUp",
                "timestamp_right": "last_event_timestamp",
            }
        )
        .select(bronze_pdr_slots_schema.keys())
    )
    # remove duplicate IDs
    slots_df = slots_df.sort("timestamp").unique(subset=["ID"])

    # update dfs
    tables[bronze_pdr_slots_table_name].df = slots_df.sort("timestamp")
    return tables


@enforce_types
def get_bronze_pdr_slots_table(gql_tables: Dict[str, Table], ppss: PPSS) -> Table:
    """
    @description
        Updates/Creates clean slots from existing raw tables
    """

    collision_ids: pl.Series = pl.Series([])
    # retrieve pred ids that are already in the lake
    if len(gql_tables[bronze_pdr_slots_table_name].df) > 0:
        collision_ids = gql_tables[bronze_pdr_slots_table_name].df.filter(
            (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
            & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        )["ID"]

    # do post sync processing
    gql_tables = _process_slots(collision_ids, gql_tables, ppss)
    gql_tables = _process_truevals(gql_tables, ppss)
    gql_tables = _process_bronze_predictions(gql_tables, ppss)
    gql_tables = _process_payouts(gql_tables, ppss)

    # after all post processing, return bronze_slots
    return gql_tables[bronze_pdr_slots_table_name]
