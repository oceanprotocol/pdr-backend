from enforce_typing import enforce_types

import polars as pl
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.table_bronze_pdr_slots import (
    get_bronze_pdr_slots_df,
    bronze_pdr_slots_schema,
)
from pdr_backend.lake.table_bronze_pdr_predictions import (
    get_bronze_pdr_predictions_df,
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

    # Create bronze slots table
    gql_dfs["bronze_pdr_slots"] = get_bronze_pdr_slots_df(gql_dfs, ppss)
    assert gql_dfs["bronze_pdr_slots"].schema == bronze_pdr_slots_schema

    # Create bronze predictions table
    gql_dfs["bronze_pdr_predictions"] = get_bronze_pdr_predictions_df(gql_dfs, ppss)
    assert gql_dfs["bronze_pdr_predictions"].schema == bronze_pdr_predictions_schema
