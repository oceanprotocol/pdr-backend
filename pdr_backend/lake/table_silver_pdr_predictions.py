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
    collision_obj: object, tables: Dict[str, Table], ppss: PPSS
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
        & (
            (pl.col("ID").is_in(list(map(str, collision_obj.keys())))).not_()
            | pl.col("last_event_timestamp")
            .eq(
                pl.col("ID")
                .map_elements(lambda x: collision_obj.get(str(x), None))
                .cast(pl.Int64())
            )
            .not_()
        )
    )

    if len(bronze_pdr_predictions) == 0:
        return tables

    silver_predictions_df = tables[silver_pdr_predictions_table_name].df

    for row in bronze_pdr_predictions.rows(named=True):
        # Sort by latest timestamp then use groupby to get the first row for each user and contract combination
        result_df = silver_predictions_df.sort("slot", descending=True).filter(
            (pl.col("user") == row["user"])
            & (pl.col("contract") == row["contract"])
            & (pl.col("slot") < row["slot"])
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

        existing_prediction_df = silver_predictions_df.filter(
            pl.col("slot") == row["slot"]
        )
        if len(existing_prediction_df) > 0:
            silver_predictions_df = silver_predictions_df.filter(
                pl.col("ID") != row["ID"]
            )

        new_row_df = pl.DataFrame(row, silver_pdr_predictions_schema)
        new_row_df.select(silver_pdr_predictions_schema)
        silver_predictions_df.extend(new_row_df)

        if len(existing_prediction_df) > 0:
            # Iterate through the DataFrame and update rows
            dfs_to_update = silver_predictions_df.sort("slot").filter(
                (pl.col("user") == row["user"])
                & (pl.col("contract") == row["contract"])
                & (pl.col("slot") > row["slot"])
            )
            result_df = row

            for row_to_update in dfs_to_update.rows(named=True):
                row_to_update["sum_stake"] = (
                    result_df["sum_stake"] + row_to_update["stake"]
                    if row_to_update["stake"]
                    else 0
                )
                row_to_update["sum_revenue"] = result_df["sum_revenue"] + (
                    row_to_update["payout"] if row_to_update["payout"] else 0
                )
                row_to_update["sum_revenue_df"] = (
                    result_df["sum_revenue_df"] + row_to_update["payout"]
                )
                row_to_update["sum_revenue_stake"] = (
                    result_df["sum_revenue_stake"] + row_to_update["payout"]
                )
                row_to_update["count_predictions"] = result_df["count_predictions"] + 1
                row_to_update["count_wins"] = result_df["count_wins"] + (
                    1 if row_to_update["predvalue"] == row_to_update["truevalue"] else 0
                )
                row_to_update["count_losses"] = result_df["count_losses"] + (
                    0 if row_to_update["predvalue"] == row_to_update["truevalue"] else 1
                )
                row_to_update["win"] = (
                    row_to_update["sum_revenue"] > row_to_update["sum_stake"]
                )

                silver_predictions_df = silver_predictions_df.filter(
                    pl.col("ID") != row_to_update["ID"]
                )
                new_row_df = pl.DataFrame(row_to_update, silver_pdr_predictions_schema)
                new_row_df.select(silver_pdr_predictions_schema)
                silver_predictions_df.extend(new_row_df)

    print(silver_predictions_df["sum_revenue"].to_list)

    tables[silver_pdr_predictions_table_name].df = silver_predictions_df.sort("slot")
    return tables


@enforce_types
def get_silver_pdr_predictions_table(gql_tables: Dict[str, Table], ppss: PPSS) -> Table:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """

    collision_obj: object = {}
    # retrieve pred ids that are already in the lake
    if len(gql_tables[silver_pdr_predictions_table_name].df) > 0:
        filtered_table = gql_tables[silver_pdr_predictions_table_name].df.filter(
            (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
            & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
        )
        if len(filtered_table) > 0:
            for row in filtered_table.rows(named=True):
                collision_obj[row["ID"]] = row["last_event_timestamp"]

    # do post sync processing
    gql_tables = _process_predictions(collision_obj, gql_tables, ppss)

    # after all post processing, return bronze_predictions
    return gql_tables[silver_pdr_predictions_table_name]
