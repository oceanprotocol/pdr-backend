from unittest.mock import patch, Mock
import dash

from enforce_typing import enforce_types
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    _query_db,
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
    select_or_clear_all_by_table,
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
    ppss, _ = _prepare_test_db(
        tmpdir, _sample_payouts, table_name=Payout.get_lake_table_name()
    )

    result = get_payouts_from_db([], [], ppss.lake_ss.lake_dir)

    assert len(result) == 0

    result = get_payouts_from_db(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        ppss.lake_ss.lake_dir,
    )

    assert isinstance(result, list)
    assert len(result) == 2

    _clear_test_db(ppss.lake_ss.lake_dir)


def test_select_all(sample_table_rows):
    # Mock the dash callback context
    mock_ctx = Mock()
    mock_ctx.triggered = [{"prop_id": "select-all-example-table.n_clicks"}]

    result = select_or_clear_all_by_table(mock_ctx, "example-table", sample_table_rows)

    assert result == list(
        range(len(sample_table_rows))
    ), "The select all function did not return the expected indices."


def test_no_trigger(sample_table_rows):
    # Mock the dash callback context with no trigger
    mock_ctx = Mock()
    mock_ctx.triggered = []

    result = select_or_clear_all_by_table(mock_ctx, "example-table", sample_table_rows)

    assert (
        result == dash.no_update
    ), "The function should return no_update when there is no trigger."


def test_unrelated_trigger(sample_table_rows):
    # Mock the dash callback context with an unrelated trigger
    mock_ctx = Mock()
    mock_ctx.triggered = [{"prop_id": "some-other-button.n_clicks"}]

    result = select_or_clear_all_by_table(mock_ctx, "example-table", sample_table_rows)

    assert (
        result == []
    ), "The function should return an empty list for unrelated triggers."
