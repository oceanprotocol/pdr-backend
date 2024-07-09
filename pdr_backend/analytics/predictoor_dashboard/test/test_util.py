from unittest.mock import patch

from enforce_typing import enforce_types
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    _query_db,
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
)

from pdr_backend.analytics.predictoor_dashboard.test.resources import (
    _prepare_test_db,
    _clear_test_db,
)
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.payout import Payout


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
def test_get_feeds_data_from_db(
    tmpdir,
    _sample_first_predictions,
):
    ppss, sample_data_df = _prepare_test_db(
        tmpdir, _sample_first_predictions, Prediction.get_lake_table_name()
    )

    result = get_feeds_data_from_db(ppss.lake_ss.lake_dir)

    assert isinstance(result, list)
    assert len(result) == len(sample_data_df)

    _clear_test_db(ppss.lake_ss.lake_dir)


@enforce_types
def test_get_predictoors_data_from_db(
    tmpdir,
    _sample_first_predictions,
):
    ppss, sample_data_df = _prepare_test_db(
        tmpdir, _sample_first_predictions, Prediction.get_lake_table_name()
    )

    result = get_predictoors_data_from_db(ppss.lake_ss.lake_dir)

    grouped_sample = sample_data_df.unique("user")

    assert isinstance(result, list)
    assert len(result) == len(grouped_sample)

    _clear_test_db(ppss.lake_ss.lake_dir)


@enforce_types
def test_get_payouts_from_db(
    tmpdir,
    _sample_payouts,
):
    ppss, _ = _prepare_test_db(tmpdir, _sample_payouts, table_name="pdr_payouts")

    result = get_payouts_from_db([], [], ppss.lake_ss.lake_dir)

    print("result--->", result)
    assert len(result) == 0

    result = get_payouts_from_db(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        ppss.lake_ss.lake_dir,
    )

    assert isinstance(result, list)
    assert len(result) == 2

    _clear_test_db(ppss.lake_ss.lake_dir)
