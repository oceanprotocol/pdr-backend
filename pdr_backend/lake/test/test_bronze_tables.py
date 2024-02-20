from enforce_typing import enforce_types

import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    get_bronze_pdr_slots_table,
    bronze_pdr_slots_schema,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_table,
    bronze_pdr_predictions_schema,
)


@enforce_types
def test_bronze_tables_coraltion(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
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

    gql_dfs = {
        "pdr_slots": _gql_datafactory_etl_slots_df,
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
        "pdr_payouts": _gql_datafactory_etl_payouts_df,
        "bronze_pdr_predictions": pl.DataFrame(),
        "bronze_pdr_slots": pl.DataFrame(),
    }

    # Create bronze predictions table
    bronze_pdr_prediction_table = get_bronze_pdr_predictions_table(gql_dfs, ppss)

    # Validate bronze_pdr_prediction_table is correct, and as expected
    assert gql_dfs["bronze_pdr_predictions"].schema == bronze_pdr_predictions_schema
    assert len(gql_dfs["bronze_pdr_predictions"]) == 6

    # Create bronze slots table
    gql_dfs["bronze_pdr_slots"] = get_bronze_pdr_slots_table(gql_dfs, ppss)
    assert gql_dfs["bronze_pdr_slots"].schema == bronze_pdr_slots_schema
    assert len(gql_dfs["bronze_pdr_slots"]) == 6

    # Get predictions data from predictions table for slots within slots table
    slots_with_predictions_df = gql_dfs["bronze_pdr_slots"].join(
        gql_dfs["bronze_pdr_predictions"].select(
            ["slot", "user", "payout", "predvalue"]
        ),
        on=["slot"],
        how="left",
    )

    users = slots_with_predictions_df["user"].to_list()
    assert len(users) == 6

    predvalues = slots_with_predictions_df["predvalue"].to_list()
    assert len(predvalues) == 6

    payouts = slots_with_predictions_df["payout"].to_list()
    assert len(payouts) == 6

    # filter data frame by slot
    filtered_by_slot = slots_with_predictions_df.filter(
        slots_with_predictions_df["slot"] == 1698951600
    )

    # create lists of payouts and users for selected slot
    payouts_for_slot = filtered_by_slot["payout"].to_list()
    users_for_slot = filtered_by_slot["user"].to_list()

    assert len(payouts_for_slot) == 1
    assert int(payouts_for_slot[0]) == 10

    assert len(users_for_slot) == len(payouts_for_slot)
    assert users_for_slot[0] == "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd"
