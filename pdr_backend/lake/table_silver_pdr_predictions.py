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
    "sum_stake": Float64,
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

    silver_predictions_df = tables[silver_pdr_predictions_table_name].df

    print(bronze_pdr_predictions)

    for row in bronze_pdr_predictions.rows(named=True):
        # Sort by latest timestamp then use groupby to get the first row for each user and contract combination
        result_df = silver_predictions_df.sort("timestamp", descending=True).filter(
            (pl.col("user") == row["user"]) & (pl.col("contract") == row["contract"])
        )[0]
        if len(result_df) > 0:
            row["sum_stake"] = (
                result_df["sum_stake"] + row["stake"] if row["stake"] else 0
            )
            row["sum_revenue"] = result_df["sum_revenue"] + (
                row["payout"] if row["payout"] else 0
            )
            row["sum_revenue_df"] = result_df["sum_revenue_df"] + row["payout"]
            row["sum_revenue_stake"] = result_df["sum_revenue_stake"] + row["payout"]
            row["count_predictions"] = result_df["count_predictions"] + 1
            row["count_wins"] = result_df["count_wins"] + (
                1 if row["predvalue"] == row["truevalue"] else 0
            )
            row["count_losses"] = result_df["count_losses"] + (
                0 if row["predvalue"] == row["truevalue"] else 1
            )
            row["win"] = row["sum_revenue"] > row["sum_stake"]
        else:
            row["sum_stake"] = row["stake"] if row["stake"] else 0
            row["sum_revenue"] = row["payout"] if row["payout"] else 0
            row["sum_revenue_df"] = row["payout"]
            row["sum_revenue_stake"] = row["payout"]
            row["count_predictions"] = 1
            row["count_wins"] = 1 if row["predvalue"] == row["truevalue"] else 0
            row["count_losses"] = 0 if row["predvalue"] == row["truevalue"] else 1
            row["win"] = row["sum_revenue"] > row["sum_stake"]
        new_row_df = pl.DataFrame(row, silver_pdr_predictions_schema)
        new_row_df.select(silver_pdr_predictions_schema).sort("timestamp")
        silver_predictions_df.extend(new_row_df)

    tables[silver_pdr_predictions_table_name].df = silver_predictions_df
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
