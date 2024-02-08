from enforce_typing import enforce_types

import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    _process_predictions,
    _process_slots,
    _process_truevals,
    bronze_pdr_slots_schema,
)


@enforce_types
def test_table_bronze_pdr_slots(
    _gql_datafactory_etl_slots_df,
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
        "pdr_slots": _gql_datafactory_etl_slots_df,
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
        "bronze_pdr_slots": pl.DataFrame(),
    }

    assert len(gql_dfs["bronze_pdr_slots"]) == 0

    # Work 1: Append new slots onto bronze_table
    # In our mock, all predictions have None trueval, predictions, etc...
    # This shows that all of this data will come from other tables
    gql_dfs = _process_slots([], gql_dfs, ppss)
    assert len(gql_dfs["bronze_pdr_slots"]) == 6
    assert gql_dfs["bronze_pdr_slots"]["slot"] is not None
    assert gql_dfs["bronze_pdr_slots"]["timestamp"] is not None
    assert gql_dfs["bronze_pdr_slots"]["roundSumStakesUp"] is not None
    assert gql_dfs["bronze_pdr_slots"]["roundSumStakes"] is not None

    # Work 2: Append from pdr_truevals table
    gql_dfs = _process_truevals(gql_dfs, ppss)

    assert len(gql_dfs["bronze_pdr_slots"]) == 6

    # Work 3: Append from pdr_predictions table
    gql_dfs = _process_predictions(gql_dfs, ppss)

    # We should still have 6 rows
    assert len(gql_dfs["bronze_pdr_slots"]) == 6

    # Check final data frame has all the required columns
    assert gql_dfs["bronze_pdr_slots"].schema == bronze_pdr_slots_schema
