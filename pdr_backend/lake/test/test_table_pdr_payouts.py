from typing import List
from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.table_pdr_payouts import payouts_schema
from pdr_backend.lake.test.resources import _gql_data_factory, _filter_gql_tables_config
from pdr_backend.util.timeutil import timestr_to_ut

# ====================================================================
pdr_payouts_record = "pdr_payouts"


@patch("pdr_backend.lake.table_pdr_payouts.fetch_payouts")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_update_payout_gql_proxy(
    mock_get_all_contract_ids_by_owner, mock_fetch_payouts, tmpdir, sample_payouts
):
    st_timestr = "2023-01-01_0:00"
    fin_timestr = "2024-01-04_17:00"
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    _test_update_payout_gql(
        mock_fetch_payouts,
        tmpdir,
        sample_payouts,
        st_timestr,  # earlier date
        fin_timestr,  # later date
        n_items=6,
    )


@enforce_types
def _test_update_payout_gql(
    mock_fetch_payouts,
    tmpdir,
    subgraph_payouts,
    st_timestr: str,
    fin_timestr: str,
    n_items: int,
):
    """
    @arguments
      n_items -- expected # payouts. Typically int. If '>1K', expect >1000
    """

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update subscriptions record only
    default_config = gql_data_factory.record_config
    gql_data_factory.record_config["tables"] = _filter_gql_tables_config(
        gql_data_factory.record_config, pdr_payouts_record
    )

    payouts_table = gql_data_factory.get_gql_tables()["pdr_payouts"]
    fin_ut = timestr_to_ut(fin_timestr)
    st_ut = payouts_table._calc_start_ut(payouts_table.table_name)

    # calculate ms locally so we can filter raw subscriptions
    st_ut_sec = st_ut // 1000
    fin_ut_sec = fin_ut // 1000

    mock_fetch_payouts.return_value = subgraph_payouts

    # work 1: update parquet
    gql_data_factory._update()

    # assert params
    mock_fetch_payouts.assert_called_with(
        ["0x123"],
        st_ut_sec,
        fin_ut_sec,
        0,
        "mainnet",
    )

    # setup: filename
    # everything will be inside the gql folder
    filename = payouts_table._parquet_filename()
    assert ".parquet" in filename

    # read parquet and columns
    def _payouts_in_parquet(filename: str) -> List[int]:
        df = pl.read_parquet(filename)
        assert df.schema == payouts_schema
        return df["timestamp"].to_list()

    # assert expected length of payouts in parquet
    payouts: List[int] = _payouts_in_parquet(filename)
    if isinstance(n_items, int):
        assert len(payouts) == n_items
    elif n_items == ">1K":
        assert len(payouts) > 1000

    # reset record config
    gql_data_factory.record_config = default_config


@patch("pdr_backend.lake.table_pdr_payouts.fetch_payouts")
@patch("pdr_backend.lake.gql_data_factory.get_all_contract_ids_by_owner")
def test_load_and_verify_payout_schema(
    mock_get_all_contract_ids_by_owner, mock_fetch_payouts, tmpdir, sample_payouts
):
    mock_get_all_contract_ids_by_owner.return_value = ["0x123"]
    st_timestr = "2023-01-01_0:00"
    fin_timestr = "2024-01-04_17:00"

    _test_update_payout_gql(
        mock_fetch_payouts,
        tmpdir,
        sample_payouts,
        st_timestr,  # earlier date
        fin_timestr,  # later date
        n_items=6,
    )

    _, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    # Update subscriptions record only
    gql_data_factory.record_config["tables"] = _filter_gql_tables_config(
        gql_data_factory.record_config, pdr_payouts_record
    )

    tables = gql_data_factory.get_gql_tables()

    assert len(tables.items()) == 1
    assert len(tables[pdr_payouts_record].df) == 6
    assert round(tables[pdr_payouts_record].df["payout"].sum(), 0) == 15.0
    assert tables[pdr_payouts_record].df.schema == payouts_schema
