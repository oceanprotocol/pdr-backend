from typing import List
from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.table_pdr_subscriptions import subscriptions_schema
from pdr_backend.lake.test.resources import _gql_data_factory, _filter_gql_config
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.util.timeutil import timestr_to_ut

# ====================================================================
pdr_subscriptions_record = "pdr_subscriptions"


@patch("pdr_backend.lake.table_pdr_subscriptions.fetch_filtered_subscriptions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql1(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_subscriptions,
    tmpdir,
    sample_subscriptions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_gql(
        mock_fetch_filtered_subscriptions,
        tmpdir,
        sample_subscriptions,
        "2023-11-02_0:00",
        "2023-11-04_17:00",
        n_subs=4,
    )


@patch("pdr_backend.lake.table_pdr_subscriptions.fetch_filtered_subscriptions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_gql_iteratively(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_subscriptions,
    tmpdir,
    sample_subscriptions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    iterations = [
        ("2023-11-02_0:00", "2023-11-04_17:00", 4),
        ("2023-11-01_0:00", "2023-11-04_17:00", 4),  # does not append to beginning
        ("2023-11-01_0:00", "2023-11-05_17:00", 6),
        ("2023-11-01_0:00", "2023-11-06_17:00", 7),
    ]

    for st_timestr, fin_timestr, n_subs in iterations:
        _test_update_gql(
            mock_fetch_filtered_subscriptions,
            tmpdir,
            sample_subscriptions,
            st_timestr,
            fin_timestr,
            n_subs=n_subs,
        )


@enforce_types
def _test_update_gql(
    mock_fetch_filtered_subscriptions,
    tmpdir,
    sample_subscriptions,
    st_timestr: str,
    fin_timestr: str,
    n_subs,
):
    """
    @arguments
      n_subs -- expected # subscriptions. Typically int. If '>1K', expect >1000
    """

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update subscriptions record only
    default_config = gql_data_factory.record_config
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_subscriptions_record
    )

    # setup: filename
    # everything will be inside the gql folder
    filename = gql_data_factory._parquet_filename(pdr_subscriptions_record)
    assert ".parquet" in filename

    fin_ut = timestr_to_ut(fin_timestr)
    st_ut = gql_data_factory._calc_start_ut(filename)

    # calculate ms locally so we can filter raw subscriptions
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    # filter subs that will be returned from subgraph to client
    target_subs = [
        x for x in sample_subscriptions if st_ut_sec <= x.timestamp <= fin_ut_sec
    ]
    mock_fetch_filtered_subscriptions.return_value = target_subs

    # work 1: update parquet
    gql_data_factory._update(fin_ut)

    # assert params
    mock_fetch_filtered_subscriptions.assert_called_with(
        st_ut_sec,
        fin_ut_sec,
        ["0x123"],
        "mainnet",
    )

    # read parquet and columns
    def _subs_in_parquet(filename: str) -> List[int]:
        df = pl.read_parquet(filename)
        assert df.schema == subscriptions_schema
        return df["timestamp"].to_list()

    # assert expected length of subs in parquet
    subs: List[int] = _subs_in_parquet(filename)
    if isinstance(n_subs, int):
        assert len(subs) == n_subs
    elif n_subs == ">1K":
        assert len(subs) > 1000

    # subs may not match start or end time
    assert subs[0] != st_ut
    assert subs[-1] != fin_ut

    # assert all target_subs are registered in parquet
    target_subs_ts = [sub.__dict__["timestamp"] for sub in target_subs]
    for target_sub in target_subs_ts:
        assert target_sub * 1000 in subs

    # reset record config
    gql_data_factory.record_config = default_config


@patch("pdr_backend.lake.table_pdr_subscriptions.fetch_filtered_subscriptions")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_and_verify_schema(
    mock_get_all_contract_ids_by_owner,
    mock_fetch_filtered_subscriptions,
    tmpdir,
    sample_subscriptions,
    monkeypatch,
):
    del_network_override(monkeypatch)
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    st_timestr = "2023-11-01_0:00"
    fin_timestr = "2023-11-07_0:00"

    _test_update_gql(
        mock_fetch_filtered_subscriptions,
        tmpdir,
        sample_subscriptions,
        st_timestr,
        fin_timestr,
        n_subs=8,
    )

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update subscriptions record only
    gql_data_factory.record_config = _filter_gql_config(
        gql_data_factory.record_config, pdr_subscriptions_record
    )

    fin_ut = timestr_to_ut(fin_timestr)
    gql_dfs = gql_data_factory._load_parquet(fin_ut)

    assert len(gql_dfs) == 1
    assert len(gql_dfs[pdr_subscriptions_record]) == 8
    assert round(gql_dfs[pdr_subscriptions_record]["last_price_value"].sum(), 2) == 24.0
    assert gql_dfs[pdr_subscriptions_record].schema == subscriptions_schema
