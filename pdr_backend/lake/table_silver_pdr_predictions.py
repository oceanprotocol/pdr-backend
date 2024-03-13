from typing import Dict, Tuple

import polars as pl
from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8, DataFrame
from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.constants_opf_addrs import get_opf_addresses


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
    "sum_revenue_user": Float64,
    "sum_revenue_stake": Float64,
    "win": Boolean,
    "count_wins": Int64,
    "count_losses": Int64,
    "count_predictions": Int64,
    "timestamp": Int64,
    "last_event_timestamp": Int64,
}

timeframe_to_seconds = {
    "5m": 300,
    "1h": 3600
}

def update_fields(
    current_df: dict,
    previous_df: DataFrame,
    df_subscriptions: DataFrame,
    user_subscriptions: DataFrame,
    df_slots: DataFrame,
) -> dict:
    SECONDS_IN_24h = 86400
    if (current_df["predvalue"] == current_df["truevalue"]) & (
        current_df["truevalue"] is not None
    ):
        slot_revenue_from_df = df_subscriptions.filter(
            (pl.col("timestamp") < (current_df["slot"] * 1000))
            & ((pl.col("timestamp") + (SECONDS_IN_24h * 1000)) > (current_df["slot"] * 1000))
            & (pl.col("pair") == current_df["pair"])
            & (pl.col("timeframe") == current_df["timeframe"])
        ).with_columns(pl.col("last_price_value").sum().alias("sum_revenue"))
        slot_revenue_from_user = user_subscriptions.filter(
            (pl.col("timestamp") < (current_df["slot"] * 1000))
            & ((pl.col("timestamp") + (SECONDS_IN_24h * 1000)) > (current_df["slot"] * 1000))
            & (pl.col("pair") == current_df["pair"])
            & (pl.col("timeframe") == current_df["timeframe"])
        ).with_columns(pl.col("last_price_value").sum().alias("sum_revenue"))
        df_revenue = 0
        user_revenue = 0
        print(slot_revenue_from_df, slot_revenue_from_user)
        if (len(slot_revenue_from_df) > 0) or (len(slot_revenue_from_user) > 0):
            print(slot_revenue_from_df[0]["sum_revenue"][0], SECONDS_IN_24h, timeframe_to_seconds[current_df["timeframe"]])
            print(slot_revenue_from_df[0]["sum_revenue"][0] / (SECONDS_IN_24h / timeframe_to_seconds[current_df["timeframe"]]))
            print(current_df["payout"])
            slot_df = df_slots.filter(pl.col("ID") == (current_df["contract"] + "-" + str(current_df["slot"])))
            df_revenue, user_revenue = get_df_revenue_for_slot(
                current_df,
                slot_revenue_from_df[0]["sum_revenue"][0] / (SECONDS_IN_24h / timeframe_to_seconds[current_df["timeframe"]]),
                slot_revenue_from_user[0]["sum_revenue"][0] / (SECONDS_IN_24h / timeframe_to_seconds[current_df["timeframe"]]),
                slot_df,
            )
            print(df_revenue, user_revenue)
        current_df["sum_revenue"] = (
            previous_df["sum_revenue"] + current_df["payout"]
            if current_df["payout"]
            else 0
        )
        current_df["sum_revenue_df"] = previous_df["sum_revenue_df"] + df_revenue
        current_df["sum_revenue_user"] = previous_df["sum_revenue_user"] + user_revenue
        current_df["sum_revenue_stake"] = (
            previous_df["sum_revenue_stake"]
            + (current_df["payout"] if current_df["payout"] else 0)
            - (df_revenue + user_revenue)
        )
    else:
        current_df["sum_revenue"] = previous_df["sum_revenue"]
        current_df["sum_revenue_df"] = previous_df["sum_revenue_df"]
        current_df["sum_revenue_user"] = previous_df["sum_revenue_user"]
        current_df["sum_revenue_stake"] = previous_df["sum_revenue_stake"]
    current_df["sum_stake"] = (
        previous_df["sum_stake"] + current_df["stake"] if current_df["stake"] else 0
    )
    current_df["count_predictions"] = previous_df["count_predictions"] + 1
    current_df["count_wins"] = previous_df["count_wins"] + (
        1 if current_df["predvalue"] == current_df["truevalue"] else 0
    )
    current_df["count_losses"] = previous_df["count_losses"] + (
        0 if current_df["predvalue"] == current_df["truevalue"] else 1
    )
    current_df["win"] = current_df["sum_revenue"] > current_df["sum_stake"]
    return current_df


def get_df_revenue_for_slot(
    current_df: dict,
    slot_revenue_from_df: int,
    slot_revenue_from_user: int,
    current_slot: DataFrame,
) -> Tuple[int, int]:
    if(len(current_slot["trueval"]) == 0):
        return 0, 0
    total_stakes = (
        current_slot["roundSumStakesUp"]
        if current_slot["trueval"][0]
        else current_slot["roundSumStakes"] - current_slot["roundSumStakesUp"]
    )
    print(current_slot["roundSumStakesUp"], current_slot["roundSumStakes"] - current_slot["roundSumStakesUp"])
    print(total_stakes, slot_revenue_from_df, slot_revenue_from_user)
    basic_payout = user_payout = current_df["stake"] * (current_slot["roundSumStakes"]) / total_stakes
    print("basic payout", basic_payout[0])
    df_payout = current_df["stake"] * (current_slot["roundSumStakes"] + slot_revenue_from_df) / total_stakes
    user_payout = current_df["stake"] * (current_slot["roundSumStakes"] + slot_revenue_from_user) / total_stakes
    print(basic_payout[0], df_payout[0])
    return (df_payout[0] - basic_payout[0]), (user_payout[0] - basic_payout[0])


def _process_predictions(
    collision_obj: dict, tables: Dict[str, Table], ppss: PPSS
) -> Dict[str, Table]:
    """
    @description
        Perform post-fetch processing on the data.
        1. Find predictions within the update
        2. Transform predictions to bronze
        3. Concat to existing table
    """

    df_subscription_addresses = []
    df_subscription_addresses.append(get_opf_addresses("sapphire-mainnet")["dfbuyer"])
    df_subscription_addresses.append(get_opf_addresses("sapphire-mainnet")["websocket"])

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

    slots_df = tables["pdr_slots"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
    )

    subscriptions_df = tables["pdr_subscriptions"].df.filter(
        (pl.col("timestamp") >= ppss.lake_ss.st_timestamp)
        & (pl.col("timestamp") <= ppss.lake_ss.fin_timestamp)
    )

    data_farming_subscriptions_df = subscriptions_df.filter(
        pl.col("user").is_in(df_subscription_addresses)
    )

    subscriptions_df = subscriptions_df.filter(
        pl.col("user").is_in(df_subscription_addresses).not_()
    )

    if len(bronze_pdr_predictions) == 0:
        return tables

    silver_predictions_df = tables[silver_pdr_predictions_table_name].df

    for row in bronze_pdr_predictions.rows(named=True):
        # Sort to get lettest prediction before current one
        result_df = silver_predictions_df.sort("slot", descending=True).filter(
            (pl.col("user") == row["user"])
            & (pl.col("contract") == row["contract"])
            & (pl.col("slot") < row["slot"])
        )[0]

        if len(result_df) > 0:
            row = update_fields(
                row,
                result_df,
                data_farming_subscriptions_df,
                subscriptions_df,
                slots_df,
            )
        else:
            row["sum_stake"] = row["stake"] if row["stake"] else 0
            row["sum_revenue"] = row["payout"] if row["payout"] else 0
            row["sum_revenue_df"] = row["payout"]
            row["sum_revenue_user"] = row["payout"]
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
            result_df = pl.DataFrame(row, silver_pdr_predictions_schema)
            for row_to_update in dfs_to_update.rows(named=True):
                new_row_df = pl.DataFrame(
                    update_fields(
                        row_to_update,
                        result_df,
                        data_farming_subscriptions_df,
                        subscriptions_df,
                        slots_df,
                    ),
                    silver_pdr_predictions_schema,
                )
                result_df = new_row_df

                silver_predictions_df = silver_predictions_df.filter(
                    pl.col("ID") != row_to_update["ID"]
                )
                new_row_df.select(silver_pdr_predictions_schema)
                silver_predictions_df.extend(new_row_df)

    tables[silver_pdr_predictions_table_name].df = silver_predictions_df.sort("slot")
    return tables


@enforce_types
def get_silver_pdr_predictions_table(gql_tables: Dict[str, Table], ppss: PPSS) -> Table:
    """
    @description
        Updates/Creates clean predictions from existing raw tables
    """

    collision_obj: dict = {}
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
