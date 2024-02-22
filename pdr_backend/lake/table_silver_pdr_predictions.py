from typing import Dict

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8
from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS


silver_pdr_predictions_table_name = "silver_pdr_predictions"

# JOIN DATA TO ENRICHED PREDICTOOR PREDICTIONS SCHEMA
silver_pdr_predictions_schema = {
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
    "sum_revenue": Float64,
    "sum_revenue_df": Float64,
    "sum_revenue_stake": Float64,
    "win": Boolean,
    "count_wins": Int64,
    "count_losses": Int64,
    "count_predictions": Int64,
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
    bronze_pdr_predictions = tables["bronze_pdr_predictions"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        & (pl.col("ID").is_in(collision_ids).not_())
    )

    if len(bronze_pdr_predictions) == 0:
        return tables

    silver_predictions_df = bronze_pdr_predictions.group_by(["user", "contract"]).agg(
        pl.col("stake").sum().alias("sum_staked"),
        pl.col("payout").sum().alias("sum_revenue"),
        pl.when(pl.col("truevalue") == pl.col("predvalue"))
        .then(pl.col("stake"))
        .otherwise(0)
        .sum()
        .alias("sum_revenue_stake"),
        pl.col("predvalue").count().alias("count_predictions"),
        pl.when(pl.col("truevalue") == pl.col("predvalue"))
        .then(1)
        .otherwise(0)
        .sum()
        .alias("count_wins"),
        pl.when(pl.col("truevalue") != pl.col("predvalue"))
        .then(1)
        .otherwise(0)
        .sum()
        .alias("count_losses"),
    )
    silver_predictions_df = silver_predictions_df.with_columns(
        (pl.col("sum_revenue") - pl.col("sum_revenue_stake")).alias("sum_revenue_df")
    )
    silver_predictions_df = silver_predictions_df.with_columns(
        (pl.col("count_wins") >= pl.col("count_losses")).alias("win")
    )

    new_silver_predictions_df = silver_predictions_df.join(
        bronze_pdr_predictions, on=["user", "contract"], how="left"
    )

    tables[silver_pdr_predictions_table_name].df = new_silver_predictions_df
    return tables


@enforce_types
def get_silver_pdr_predictions_table(gql_tables: Dict[str, Table], ppss: PPSS) -> Table:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """

    collision_ids: pl.Series = pl.Series([])
    # retrieve pred ids that are already in the lake
    if len(gql_tables[silver_pdr_predictions_table_name].df) > 0:
        collision_ids = gql_tables[silver_pdr_predictions_table_name].df.filter(
            (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
            & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        )["ID"]

    # do post sync processing
    gql_tables = _process_predictions(collision_ids, gql_tables, ppss)

    # after all post processing, return bronze_predictions
    return gql_tables[silver_pdr_predictions_table_name]
