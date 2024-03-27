from enforce_typing import enforce_types
import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_table,
    bronze_pdr_predictions_schema,
    bronze_pdr_predictions_table_name,
)
from pdr_backend.lake.table_silver_pdr_predictions import (
    get_silver_pdr_predictions_table,
    silver_pdr_predictions_table_name,
    silver_pdr_predictions_schema,
)
from pdr_backend.lake.table_pdr_predictions import (
    predictions_schema,
    predictions_table_name,
)
from pdr_backend.lake.table import Table
from pdr_backend.lake.table_pdr_truevals import truevals_schema, truevals_table_name
from pdr_backend.lake.table_pdr_payouts import payouts_schema, payouts_table_name
from pdr_backend.lake.table_pdr_subscriptions import (
    subscriptions_schema,
    subscriptions_table_name,
)
from pdr_backend.lake.table_pdr_slots import (
    slots_schema,
    slots_table_name,
)


@enforce_types
def test_silver_bronze_pdr_predictions(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_subscriptions_df,
    _gql_datafactory_etl_slots_df,
    tmpdir,
):
    # please note date, including Nov 1st
    st_timestr = "2023-11-01_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, _ = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    gql_tables = {
        "pdr_predictions": Table(predictions_table_name, predictions_schema, ppss),
        "pdr_truevals": Table(truevals_table_name, truevals_schema, ppss),
        "pdr_payouts": Table(payouts_table_name, payouts_schema, ppss),
        "pdr_subscriptions": Table(
            subscriptions_table_name, subscriptions_schema, ppss
        ),
        "pdr_slots": Table(slots_table_name, slots_schema, ppss),
        "bronze_pdr_predictions": Table(
            bronze_pdr_predictions_table_name, bronze_pdr_predictions_schema, ppss
        ),
        "silver_pdr_predictions": Table(
            silver_pdr_predictions_table_name, silver_pdr_predictions_schema, ppss
        ),
    }

    gql_tables["pdr_predictions"].df = _gql_datafactory_etl_predictions_df
    gql_tables["pdr_truevals"].df = _gql_datafactory_etl_truevals_df
    gql_tables["pdr_payouts"].df = _gql_datafactory_etl_payouts_df
    gql_tables["pdr_subscriptions"].df = _gql_datafactory_etl_subscriptions_df
    gql_tables["pdr_slots"].df = _gql_datafactory_etl_slots_df
    gql_tables["bronze_pdr_predictions"].df = get_bronze_pdr_predictions_table(
        gql_tables, ppss
    ).df

    assert len(gql_tables[bronze_pdr_predictions_table_name].df) == 9

    # Check that the silver predictions table has the right schema and length
    get_silver_pdr_predictions_table(gql_tables, ppss)

    # verify predictions for give user and contract
    selected_user_prediction = (
        gql_tables[silver_pdr_predictions_table_name]
        .df.sort("timestamp", descending=True)
        .filter(
            (pl.col("user") == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd")
            & (pl.col("contract") == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695")
        )[0]
    )

    print(selected_user_prediction)
    print(gql_tables[silver_pdr_predictions_table_name].df)

    # Check payout sum
    assert (
        selected_user_prediction["sum_revenue"][0]
        == (
            _gql_datafactory_etl_payouts_df[0]["payout"][0]
            + (
                _gql_datafactory_etl_payouts_df[4]["payout"][0]
                if _gql_datafactory_etl_payouts_df[4]["payout"][0]
                else -_gql_datafactory_etl_payouts_df[4]["stake"][0]
            )
            + (
                _gql_datafactory_etl_payouts_df[5]["payout"][0]
                if _gql_datafactory_etl_payouts_df[5]["payout"][0]
                else -_gql_datafactory_etl_payouts_df[5]["stake"][0]
            )
        )
        if _gql_datafactory_etl_payouts_df[0]["payout"][0]
        else (
            selected_user_prediction["sum_revenue"][0]
            - _gql_datafactory_etl_payouts_df[0]["payout"][0]
        )
    )

    # Check number of predictions sum
    assert (
        selected_user_prediction["count_predictions"][0]
        == gql_tables[silver_pdr_predictions_table_name]
        .df.group_by("user", "contract")
        .agg(pl.col("user").count().alias("count_per_ID"))
        .filter(
            (pl.col("user") == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd")
            & (pl.col("contract") == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695")
        )[0]["count_per_ID"][0]
    )

    assert selected_user_prediction["sum_revenue_df"][0] == 2.939274921318411
    assert selected_user_prediction["sum_stake"][0] == 8.9
    """
    assert (
        selected_user_prediction["sum_revenue"][0]
        == selected_user_prediction["sum_revenue_df"][0]
        + selected_user_prediction["sum_revenue_stake"][0]
        + selected_user_prediction["sum_revenue_user"][0]
    )
    """

    # Check number of wins and losses
    assert selected_user_prediction["count_wins"][0] == 3
    assert selected_user_prediction["count_losses"][0] == 1

    # Check payout sum
    assert selected_user_prediction["sum_stake"][0] == 8.9

    # Check win of wins and losses
    assert selected_user_prediction["win"][0] is True

    assert len(gql_tables[silver_pdr_predictions_table_name].df) == 9
    assert (
        gql_tables[silver_pdr_predictions_table_name].df_schema
        == silver_pdr_predictions_schema
    )

    # Test progressive revenue sum
    selected_user_predictions = gql_tables[silver_pdr_predictions_table_name].df.filter(
        (pl.col("user") == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd")
        & (pl.col("contract") == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695")
    )
    assert selected_user_predictions[0]["sum_revenue"][0] == (
        selected_user_predictions[0]["payout"][0]
        if selected_user_predictions[0]["payout"][0]
        else (
            -selected_user_predictions[0]["stake"][0]
            if selected_user_predictions[0]["stake"][0]
            else 0
        )
    )
    assert selected_user_predictions[1]["sum_revenue"][0] == selected_user_predictions[
        0
    ]["sum_revenue"][0] + (
        (
            selected_user_predictions[1]["payout"][0]
            - selected_user_predictions[1]["stake"][0]
        )
        if selected_user_predictions[1]["payout"][0]
        else (
            -selected_user_predictions[1]["stake"][0]
            if selected_user_predictions[1]["stake"][0]
            else 0
        )
    )
    assert selected_user_predictions[2]["sum_revenue"][0] == selected_user_predictions[
        1
    ]["sum_revenue"][0] + (
        (
            selected_user_predictions[2]["payout"][0]
            - selected_user_predictions[2]["stake"][0]
        )
        if selected_user_predictions[2]["payout"][0]
        else (
            -selected_user_predictions[2]["stake"][0]
            if selected_user_predictions[2]["stake"][0]
            else 0
        )
    )
    assert selected_user_predictions[3]["sum_revenue"][0] == selected_user_predictions[
        2
    ]["sum_revenue"][0] + (
        (
            selected_user_predictions[3]["payout"][0]
            - selected_user_predictions[3]["stake"][0]
        )
        if selected_user_predictions[3]["payout"][0]
        else (
            -selected_user_predictions[3]["stake"][0]
            if selected_user_predictions[3]["stake"][0]
            else 0
        )
    )

    # Insert new prediction to bronze table
    # pylint: disable=line-too-long
    row = {
        "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "slot_id": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302700",
        "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",  # f"{contract}"
        "slot": 1699302700,
        "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "source": "binance",
        "predvalue": None,
        "truevalue": False,
        "stake": None,
        "payout": None,
        "timestamp": 1699302700000,
        "last_event_timestamp": 1699302700000,
    }
    row2 = {
        "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302800-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "slot_id": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302800",
        "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",  # f"{contract}"
        "slot": 1699302800,
        "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "source": "binance",
        "predvalue": True,
        "truevalue": True,
        "stake": 11.00000023,
        "payout": 35.00000023,
        "timestamp": 1699302800000,
        "last_event_timestamp": 1699302800000,
    }
    row3 = {
        "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302900-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "slot_id": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302900",
        "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",  # f"{contract}"
        "slot": 1699302900,
        "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "source": "binance",
        "predvalue": True,
        "truevalue": False,
        "stake": 20,
        "payout": 20,
        "timestamp": 1699302900000,
        "last_event_timestamp": 1699302900000,
    }
    new_row_df = pl.DataFrame(row, bronze_pdr_predictions_schema)
    new_row_df2 = pl.DataFrame(row2, bronze_pdr_predictions_schema)
    new_row_df3 = pl.DataFrame(row3, bronze_pdr_predictions_schema)
    gql_tables[bronze_pdr_predictions_table_name].df.extend(new_row_df)
    gql_tables[bronze_pdr_predictions_table_name].df.extend(new_row_df2)
    gql_tables[bronze_pdr_predictions_table_name].df.extend(new_row_df3)

    # Check that new prediction was added to bronce table
    assert len(gql_tables[bronze_pdr_predictions_table_name].df) == 12

    # Update silver predictions
    get_silver_pdr_predictions_table(gql_tables, ppss)

    # verify predictions for user=0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd , contract=0x30f1c55e72fe105e4a1fbecdff3145fc14177695
    selected_user_prediction = (
        gql_tables[silver_pdr_predictions_table_name]
        .df.sort("timestamp", descending=True)
        .filter(
            (pl.col("user") == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd")
            & (pl.col("contract") == "0x30f1c55e72fe105e4a1fbecdff3145fc14177695")
        )[0]
    )
    assert selected_user_prediction["sum_revenue"][0] == 6.555353277785645
    assert selected_user_prediction["count_wins"][0] == 4

    # if user did not call payout revenues are not calculated
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["truevalue"][0]
        != gql_tables[silver_pdr_predictions_table_name].df[9]["predvalue"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_df"][0]
        == gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_df"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_user"][0]
        == gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_user"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_stake"][0]
        == gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_stake"][0]
    )

    # Insert new prediction to bronze table
    row = {
        "ID": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "slot_id": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699302700",
        "contract": "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",  # f"{contract}"
        "slot": 1699302700,
        "user": "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "pair": "ETH/USDT",
        "timeframe": "5m",
        "source": "binance",
        "predvalue": False,
        "truevalue": False,
        "stake": 5,
        "payout": 30,
        "timestamp": 1699302700000,
        "last_event_timestamp": 1699302750000,
    }
    new_row_df = pl.DataFrame(row, bronze_pdr_predictions_schema)
    gql_tables[bronze_pdr_predictions_table_name].df.extend(new_row_df)

    # Update silver predictions
    get_silver_pdr_predictions_table(gql_tables, ppss)

    # Check that new prediction didn't change the lengts of the table
    assert len(gql_tables[silver_pdr_predictions_table_name].df) == 12

    # Check that subscription rewards are split between the 2 predictions
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[7]["sum_revenue_df"][0]
        + gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_df"][0]
        == 8.342353820800783
    )

    # if user called payout and was right revenues are not calculated
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["truevalue"][0]
        == gql_tables[silver_pdr_predictions_table_name].df[9]["predvalue"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_df"][0]
        > gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_df"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_user"][0]
        > gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_user"][0]
    )
    assert (
        gql_tables[silver_pdr_predictions_table_name].df[9]["sum_revenue_stake"][0]
        < gql_tables[silver_pdr_predictions_table_name].df[8]["sum_revenue_stake"][0]
    )
