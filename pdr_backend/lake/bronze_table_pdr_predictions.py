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
        2. Transform prediction as needed
        3. Add predictions to the existing bronze_pdr_predictions table
        4. Update predictions that already exist in the bronze_pdr_predictions table
    """
    predictions_df, predictions_ids = pick_df_and_ids_on_period(
        target=dfs["pdr_predictions"],
        start_timestamp=ppss.lake_ss.st_timestamp,
        finish_timestamp=ppss.lake_ss.fin_timestamp,
    )

    def get_contract(row) -> str:
        contract = row.split("-")[0]
        return f"{contract}"

    def get_slot_id(row) -> str:
        slot_id = row.split("-")[0] + "-" + row.split("-")[1]
        return f"{slot_id}"

    # transform from raw to bronze prediction
    bronze_predictions_df = predictions_df.with_columns(
        [
            pl.col("ID")
            .map_elements(get_contract, return_dtype=Utf8)
            .alias("contract"),
            pl.col("ID").map_elements(get_slot_id, return_dtype=Utf8).alias("slot_id"),
            pl.col("prediction").alias("predvalue"),
            pl.col("trueval").alias("truevalue"),
            pl.lit(None).alias("revenue"),
        ]
    ).select(bronze_pdr_predictions_schema)

    # Append new predictions
    # Upsert existing predictions
    # print(f'>>>>>bronze_predictions_df<<<<< {bronze_predictions_df}')

    # df = dfs[bronze_pdr_predictions_table_name]
    # print(f">>>>>>bronze_pdr_predictions_table_name<<<<<: {df.columns}")

    # df = df.join(bronze_predictions_df, left_on="ID", right_on="ID", how="left")
    # print(f">>>>>>joined bronze_pdr_predictions<<<<<: {df}")

    dfs[bronze_pdr_predictions_table_name] = bronze_predictions_df
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
    # gql_dfs = _process_payouts(gql_dfs, ppss)
    # gql_dfs = _process_truevals(gql_dfs, ppss)

    # df = _transform_timestamp_to_ms(gql_dfs[bronze_pdr_predictions_table_name])

    # # cull any records outside of our time range and sort them by timestamp
    # df = df.filter(
    #     pl.col("timestamp").is_between(
    #         ppss.lake_ss.st_timestamp, ppss.lake_ss.fin_timestamp
    #     )
    # ).sort("timestamp")

    return gql_dfs[bronze_pdr_predictions_table_name]
