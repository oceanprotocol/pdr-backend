from unittest.mock import patch
from enforce_typing import enforce_types

from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL

# ETL code-coverage
# Step 1. ETL -> do_sync_step()
# Step 2. ETL -> do_bronze_step()

# ====================================================================
# test post-fetch data processing tables


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_dfs")
def test_setup_etl(
    mock_get_gql_dfs,
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    tmpdir,
):
    # setup test
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Work 1: Initialize ETL - Assert 0 gql_dfs
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory
    assert len(etl.gql_dfs) == 0

    # Work 2: Complete ETL sync step - Assert 3 gql_dfs
    gql_dfs = {
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
        "pdr_payouts": _gql_datafactory_etl_payouts_df,
    }

    mock_get_gql_dfs.return_value = gql_dfs
    etl.do_sync_step()

    assert len(etl.gql_dfs) == 3
    assert len(etl.gql_dfs["pdr_predictions"]) == len(
        _gql_datafactory_etl_predictions_df
    )
    assert len(etl.gql_dfs["pdr_truevals"]) == len(_gql_datafactory_etl_truevals_df)
    assert len(etl.gql_dfs["pdr_payouts"]) == len(_gql_datafactory_etl_payouts_df)
