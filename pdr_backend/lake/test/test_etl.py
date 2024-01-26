from unittest.mock import patch
from enforce_typing import enforce_types

from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.lake.test.resources import _gql_data_factory
from pdr_backend.lake.etl import ETL

# ETL code-coverage
# Step 1. ETL -> do_sync_step()
# Step 2. ETL -> do_bronze_step()


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

    assert ppss.lake_ss.st_timestamp == timestr_to_ut(st_timestr)
    assert ppss.lake_ss.fin_timestamp == timestr_to_ut(fin_timestr)

    # Work 1: Initialize ETL - Assert 0 gql_dfs
    etl = ETL(ppss, gql_data_factory)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory
    assert len(etl.dfs) == 0

    # Work 2: Complete ETL sync step - Assert 3 gql_dfs
    gql_dfs = {
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
        "pdr_payouts": _gql_datafactory_etl_payouts_df,
    }
    mock_get_gql_dfs.return_value = gql_dfs
    etl.do_sync_step()

    assert len(etl.dfs) == 3
    assert len(etl.dfs["pdr_predictions"]) == 6
    assert len(_gql_datafactory_etl_predictions_df) == 6

    assert len(etl.dfs["pdr_payouts"]) == len(_gql_datafactory_etl_payouts_df)
    assert len(etl.dfs["pdr_predictions"]) == len(_gql_datafactory_etl_predictions_df)
    assert len(etl.dfs["pdr_truevals"]) == len(_gql_datafactory_etl_truevals_df)


@enforce_types
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_dfs")
def test_etl_do_bronze_step(
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

    gql_dfs = {
        "pdr_payouts": _gql_datafactory_etl_payouts_df,
        "pdr_predictions": _gql_datafactory_etl_predictions_df,
        "pdr_truevals": _gql_datafactory_etl_truevals_df,
    }
    mock_get_gql_dfs.return_value = gql_dfs

    # Work 1: Initialize ETL
    etl = ETL(ppss, gql_data_factory)

    # Work 2: Do sync
    etl.do_sync_step()

    assert len(etl.dfs["pdr_predictions"]) == 6

    # Work 3: Do bronze
    etl.do_bronze_step()

    # assert bronze_pdr_predictions_df is created
    # it should have 5 rows because of st_timestr and fin_timestr
    assert len(etl.dfs["bronze_pdr_predictions"]) == 4

    bronze_pdr_predictions_df = etl.dfs["bronze_pdr_predictions"]

    # Assert that "contract" column was created and filled correctly
    assert (
        bronze_pdr_predictions_df["contract"][0]
        == "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"
    )
    assert (
        bronze_pdr_predictions_df["contract"][0]
        == _gql_datafactory_etl_predictions_df["contract"][1]
    )
    assert (
        bronze_pdr_predictions_df["contract"][1]
        == _gql_datafactory_etl_predictions_df["contract"][2]
    )

    # Assert that the timestamp is in ms
    assert bronze_pdr_predictions_df["timestamp"][0] == 1698951500000
    assert bronze_pdr_predictions_df["timestamp"][1] == 1699037900000

    # Assert that the payout is correct
    assert round(bronze_pdr_predictions_df["payout"][0], 3) == 10.929
    assert round(bronze_pdr_predictions_df["payout"][1], 3) == 7.041

    # Assert that the last_event_timestamp == payout.timestamp
    assert bronze_pdr_predictions_df["last_event_timestamp"][0] == 1698951602000
    assert bronze_pdr_predictions_df["last_event_timestamp"][1] == 1699038002000
