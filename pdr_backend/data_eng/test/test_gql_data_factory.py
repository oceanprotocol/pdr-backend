from typing import List

from unittest.mock import patch
from enforce_typing import enforce_types
import polars as pl

from pdr_backend.data_eng.test.resources import (
    _data_gql_sources,
)
from pdr_backend.util.timeutil import (
    timestr_to_ut,
)

from pdr_backend.data_eng.gql_data_factory import (
    predictions_schema,
)

from pdr_backend.util.subgraph_predictions import (
    FilterMode,
)

# ====================================================================
# test parquet updating


@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql1(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-04_0:00",
        n_preds=2,
    )


@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql2(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-06_0:00",
        n_preds=4,
    )


@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql3(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-01_0:00",
        "2023-11-07_0:00",
        n_preds=6,
    )


@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql_multiple(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-04_0:00",
        n_preds=2,
    )

    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-01_0:00",
        "2023-11-05_0:00",
        n_preds=3,
    )

    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-07_0:00",
        n_preds=5,
    )


@enforce_types
def _test_update_gql(
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_predictions,
    st_timestr: str,
    fin_timestr: str,
    n_preds,
):
    """
    @arguments
      n_preds -- expected # predictions. Typically int. If '>1K', expect >1000
    """

    _, _, _, _, _, gql_data_factory = _data_gql_sources(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr,
        fin_timestr,
    )

    # setup: filename
    # everything will be inside the gql folder
    filename = gql_data_factory._parquet_filename("raw_predictions")
    assert "/gql/" in filename
    assert ".parquet" in filename

    fin_ut = timestr_to_ut(fin_timestr)
    st_ut = gql_data_factory._calc_start_ut(filename)

    # calculate ms locally so we can filter raw Predictions
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # filter preds that will be returned from subgraph to client
    target_preds = [
        x for x in sample_predictions if st_ut_sec <= x.timestamp <= fin_ut_sec
    ]
    mock_fetch_filtered_predictions.return_value = target_preds

    # work 1: update parquet
    gql_data_factory._update_hist_predictions(
        st_ut,
        fin_ut,
        filename,
        gql_data_factory.factory_config["raw_predictions"],
    )

    # assert params
    mock_fetch_filtered_predictions.assert_called_with(
        st_ut_sec,
        fin_ut_sec,
        ["0x123"],
        "mainnet",
        FilterMode.CONTRACT_TS,
        payout_only=False,
        trueval_only=False,
    )

    # read parquet and columns
    def _preds_in_parquet(filename: str) -> List[int]:
        df = pl.read_parquet(filename)
        assert df.schema == predictions_schema
        return df["timestamp"].to_list()

    # assert expected length of preds in parquet
    preds: List[int] = _preds_in_parquet(filename)
    if isinstance(n_preds, int):
        assert len(preds) == n_preds
    elif n_preds == ">1K":
        assert len(preds) > 1000

    # preds may not match start or end time
    assert preds[0] != st_ut
    assert preds[-1] != fin_ut

    # assert all target_preds are registered in parquet
    target_preds_ts = [pred.__dict__["timestamp"] for pred in target_preds]
    for target_pred in target_preds_ts:
        assert target_pred * 1000 in preds


@patch("pdr_backend.data_eng.gql_data_factory.fetch_filtered_predictions")
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_and_verify_schema(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
):
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        st_timestr,
        fin_timestr,
        n_preds=5,
    )

    _, _, _, _, _, gql_data_factory = _data_gql_sources(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr,
        fin_timestr,
    )

    fin_ut = timestr_to_ut(fin_timestr)
    gql_dfs = gql_data_factory._load_parquet(fin_ut)

    assert len(gql_dfs) == 1
    assert len(gql_dfs["raw_predictions"]) == 5
    assert gql_dfs["raw_predictions"].schema == predictions_schema


# ====================================================================
# test if appropriate calls are made


@enforce_types
@patch("pdr_backend.data_eng.gql_data_factory.get_all_contract_ids_by_owner")
def test_get_gql_dfs_calls(
    mock_get_all_contract_ids_by_owner, tmpdir, sample_daily_predictions
):
    """Test core DataFactory functions are being called"""
    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    _, _, _, _, _, gql_data_factory = _data_gql_sources(
        tmpdir,
        "binanceus h ETH/USDT",
        st_timestr,
        fin_timestr,
    )

    # calculate ms locally so we can filter raw Predictions
    st_ut = timestr_to_ut(st_timestr)
    fin_ut = timestr_to_ut(fin_timestr)
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # setup mock objects
    def mock_update_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_update_parquet.called = True

    def mock_load_parquet(*args, **kwargs):  # pylint: disable=unused-argument
        mock_load_parquet.called = True

        preds = [
            x
            for x in sample_daily_predictions
            if st_ut_sec <= x.timestamp <= fin_ut_sec
        ]
        preds = pl.DataFrame([x.__dict__ for x in preds])
        preds = preds.with_columns(
            [
                pl.col("timestamp").mul(1000).alias("timestamp"),
            ]
        )

        return {"raw_predictions": preds}

    gql_data_factory._update_parquet = mock_update_parquet
    gql_data_factory._load_parquet = mock_load_parquet

    # call and assert
    gql_dfs = gql_data_factory.get_gql_dfs()
    assert isinstance(gql_dfs, dict)
    assert isinstance(gql_dfs["raw_predictions"], pl.DataFrame)
    assert len(gql_dfs["raw_predictions"]) == 5

    assert mock_update_parquet.called
    assert mock_load_parquet.called
