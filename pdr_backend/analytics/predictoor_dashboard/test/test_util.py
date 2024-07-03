from unittest.mock import patch

from enforce_typing import enforce_types
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    _query_db,
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
)
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table_pdr_predictions import predictions_table_name
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_payouts import payouts_table_name


def _clear_test_db(ppss):
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    db.drop_table("pdr_payouts")
    db.drop_table("pdr_predictions")
    db.close()


def _prepare_test_db(tmpdir, sample_data, table_name=predictions_table_name):
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
    )

    db = DuckDBDataStore(str(ppss.lake_ss.lake_dir))

    sample_data_df = _object_list_to_df(sample_data)
    db.insert_to_table(
        sample_data_df,
        table_name,
    )

    db.close()

    return ppss, sample_data_df


@enforce_types
@patch(
    "pdr_backend.analytics.predictoor_dashboard.dash_components.util.DuckDBDataStore"
)
def test_query_db(
    mock_duckdb_data_store,
):
    lake_dir = "lake_dir"
    query = "query"
    _query_db(lake_dir, query)
    mock_duckdb_data_store.assert_called_once_with(lake_dir, read_only=True)
    mock_duckdb_data_store.return_value.query_data.assert_called_once_with(query)


@enforce_types
def test_get_feeds_data_from_db(tmpdir, _sample_first_predictions):
    ppss, sample_data_df = _prepare_test_db(tmpdir, _sample_first_predictions)

    result = get_feeds_data_from_db(ppss.lake_ss.lake_dir)

    assert isinstance(result, list)
    assert len(result) == len(sample_data_df)

    _clear_test_db(ppss)


@enforce_types
def test_get_predictoors_data_from_db(tmpdir, _sample_first_predictions):
    ppss, sample_data_df = _prepare_test_db(tmpdir, _sample_first_predictions)

    result = get_predictoors_data_from_db(ppss.lake_ss.lake_dir)

    grouped_sample = sample_data_df.unique("user")

    assert isinstance(result, list)
    assert len(result) == len(grouped_sample)

    _clear_test_db(ppss)


@enforce_types
def test_get_payouts_from_db(
    tmpdir,
    _sample_payouts,
):
    ppss, _ = _prepare_test_db(tmpdir, _sample_payouts, table_name=payouts_table_name)

    result = get_payouts_from_db([], [], ppss.lake_ss.lake_dir)

    assert len(result) == 0

    result = get_payouts_from_db(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        ppss.lake_ss.lake_dir,
    )

    assert isinstance(result, list)
    assert len(result) == 2

    _clear_test_db(ppss)
