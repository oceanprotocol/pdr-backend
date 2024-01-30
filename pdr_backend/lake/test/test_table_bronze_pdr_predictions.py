from unittest.mock import patch
from enforce_typing import enforce_types

import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_predictions import (
    _process_predictions,
    _process_truevals,
    _process_payouts,
)


@enforce_types
def test_table_bronze_pdr_predictions(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
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
        "pdr_payouts": _gql_datafactory_etl_payouts_df,
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
        "bronze_pdr_predictions": pl.DataFrame(),
    }

    assert len(gql_dfs["bronze_pdr_predictions"]) == 0

    # Work 1: Append new predictions onto bronze_table
    # In our mock, all predictions have None truevalue, payout, etc...
    # This shows that all of this data will come from other tables
    gql_dfs = _process_predictions(gql_dfs, ppss)
    assert len(gql_dfs["bronze_pdr_predictions"]) == 6
    assert gql_dfs["bronze_pdr_predictions"]["truevalue"].null_count() == 6
    assert gql_dfs["bronze_pdr_predictions"]["payout"].null_count() == 6

    # Work 2: Append from bronze_pdr_truevals table
    gql_dfs = _process_truevals(gql_dfs, ppss)

    # We should still have 6 rows
    assert len(gql_dfs["bronze_pdr_predictions"]) == 6
    # In our mock, we're going to have 1 truevalue missing
    assert gql_dfs["bronze_pdr_predictions"]["truevalue"].null_count() == 1

    # Work 3: Append from bronze_pdr_payouts table
    gql_dfs = _process_payouts(gql_dfs, ppss)

    assert len(gql_dfs["bronze_pdr_predictions"]) == 6

    # Assert that there could be Nones in the stake column
    assert gql_dfs["bronze_pdr_predictions"]["stake"].null_count() == 1
    target_stake = [5.46, 5.46, 3.46, 3.46, None]
    bronze_pdr_predictions_stake = gql_dfs["bronze_pdr_predictions"]["stake"].to_list()
    for actual_stake, expected_stake in zip(bronze_pdr_predictions_stake, target_stake):
        if actual_stake is None:
            assert actual_stake == expected_stake
        else:
            assert round(actual_stake, 2) == expected_stake

    # Assert that there is a None in the payout column
    assert gql_dfs["bronze_pdr_predictions"]["payout"].null_count() == 1
    target_payout = [0.00, 10.93, 7.04, 7.16, None]
    bronze_pdr_predictions_payout = gql_dfs["bronze_pdr_predictions"][
         "payout"
    ].to_list()
    for actual_payout, expected_payout in zip(
        bronze_pdr_predictions_payout, target_payout
    ):
        if actual_payout is None:
            assert actual_payout == expected_payout
        else:
            assert round(actual_payout, 2) == expected_payout
