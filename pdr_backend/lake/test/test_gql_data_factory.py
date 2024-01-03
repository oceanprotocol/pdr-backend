from typing import List
from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.table_pdr_predictions import predictions_schema
from pdr_backend.lake.test.resources import _gql_data_factory, _filter_gql_config
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.subgraph.subgraph_predictions import FilterMode
from pdr_backend.util.timeutil import timestr_to_ut

# ====================================================================
# test parquet updating
pdr_predictions_record = "pdr_predictions"


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql1(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-04_0:00",
        n_preds=2,
    )


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql2(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-02_0:00",
        "2023-11-06_0:00",
        n_preds=4,
    )


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql3(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        "2023-11-01_0:00",
        "2023-11-07_0:00",
        n_preds=6,
    )


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql_iteratively(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    iterations = [
        ("2023-11-02_0:00", "2023-11-04_0:00", 2),
        ("2023-11-01_0:00", "2023-11-05_0:00", 3),
        ("2023-11-02_0:00", "2023-11-07_0:00", 5),
    ]

    for st_timestr, fin_timestr, n_preds in iterations:
        _test_update_gql(
            mock_fetch_filtered_predictions,
            tmpdir,
            sample_daily_predictions,
            st_timestr,
            fin_timestr,
            n_preds=n_preds,
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

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update predictions record only
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    # setup: filename
    # everything will be inside the gql folder
    filename = gql_data_factory._parquet_filename(pdr_predictions_record)
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
    gql_data_factory._update(fin_ut)

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


@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_and_verify_schema(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    del_network_override(monkeypatch)
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

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    fin_ut = timestr_to_ut(fin_timestr)
    gql_dfs = gql_data_factory._load_parquet(fin_ut)

    assert len(gql_dfs) == 1
    assert len(gql_dfs[pdr_predictions_record]) == 5
    assert gql_dfs[pdr_predictions_record].schema == predictions_schema


# ====================================================================
# test if appropriate calls are made


@enforce_types
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._update")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._load_parquet")
def test_get_gql_dfs_calls(
    mock_load_parquet,
    mock_update,
    mock_get_all_contract_ids_by_owner,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    """Test core DataFactory functions are being called"""
    del_network_override(monkeypatch)

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-07_0:00"

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update predictions record only
    default_config = gql_data_factory.record_config
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_predictions_record
    )

    # calculate ms locally so we can filter raw Predictions
    st_ut = timestr_to_ut(st_timestr)
    fin_ut = timestr_to_ut(fin_timestr)
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # mock_load_parquet should return the values from a simple code block
    mock_load_parquet.return_value = {
        pdr_predictions_record: pl.DataFrame(
            [
                x.__dict__
                for x in sample_daily_predictions
                if st_ut_sec <= x.timestamp <= fin_ut_sec
            ]
        ).with_columns([pl.col("timestamp").mul(1000).alias("timestamp")])
    }

    # call and assert
    gql_dfs = gql_data_factory.get_gql_dfs()
    assert isinstance(gql_dfs, dict)
    assert isinstance(gql_dfs[pdr_predictions_record], pl.DataFrame)
    assert len(gql_dfs[pdr_predictions_record]) == 5

    mock_update.assert_called_once()
    mock_load_parquet.assert_called_once()

    # reset record config
    gql_data_factory.record_config = default_config


# ====================================================================
# test loading flow when there are pdr files missing


@enforce_types
@patch("pdr_backend.lake.table_pdr_predictions.fetch_filtered_predictions")
@patch("pdr_backend.lake.table_pdr_subscriptions.fetch_filtered_subscriptions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_missing_parquet(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_subscriptions,
    mock_fetch_filtered_predictions,
    tmpdir,
    sample_daily_predictions,
    monkeypatch,
):
    """Test core DataFactory functions are being called"""
    del_network_override(monkeypatch)

    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    mock_fetch_filtered_subscriptions.return_value = []
    mock_fetch_filtered_predictions.return_value = []

    st_timestr = "2023-11-02_0:00"
    fin_timestr = "2023-11-04_0:00"

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h",
        st_timestr,
        fin_timestr,
    )

    # Work 1: Fetch empty dataset
    # (1) perform empty fetch
    # (2) do not save to parquet
    # (3) handle missing parquet file
    # (4) assert we get empty dataframes with the expected schema
    dfs = gql_data_factory.get_gql_dfs()

    predictions_table = "pdr_predictions"
    subscriptions_table = "pdr_subscriptions"

    assert len(dfs[predictions_table]) == 0
    assert len(dfs[subscriptions_table]) == 0

    assert (
        dfs[predictions_table].schema
        == gql_data_factory.record_config[predictions_table]["schema"]
    )
    assert (
        dfs[subscriptions_table].schema
        == gql_data_factory.record_config[subscriptions_table]["schema"]
    )

    # Work 2: Fetch 1 dataset
    # (1) perform 1 successful datafactory loops (predictions)
    # (2) assert subscriptions parquet doesn't exist / has 0 records
    _test_update_gql(
        mock_fetch_filtered_predictions,
        tmpdir,
        sample_daily_predictions,
        st_timestr,
        fin_timestr,
        n_preds=2,
    )

    dfs = gql_data_factory.get_gql_dfs()
    assert len(dfs[predictions_table]) == 2
    assert len(dfs[subscriptions_table]) == 0
