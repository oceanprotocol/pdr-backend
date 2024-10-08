from unittest.mock import Mock

import dash
import polars as pl

from pdr_backend.pdr_dashboard.util.helpers import select_or_clear_all_by_table


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


def test_get_predictoors_data_from_payouts(_sample_app):
    db_mgr = _sample_app.data
    db_mgr.predictoors_data = pl.DataFrame(
        [
            {
                "user": "0x02e9d2eede4c5347e55346860c8a8988117bde9e",
                "total_profit": 0.0,
                "avg_accuracy": 100.0,
                "avg_stake": 1.9908170679122585,
            },
            {
                "user": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                "total_profit": 0.0,
                "avg_accuracy": 100.0,
                "avg_stake": 1.9908170679122585,
            },
        ]
    )

    result = db_mgr.formatted_predictoors_home_page_table_data

    assert isinstance(result, pl.DataFrame)
    assert len(result) == 2

    test_row = result.filter(
        result["full_addr"] == "0x02e9d2eede4c5347e55346860c8a8988117bde9e"
    ).to_dicts()[0]

    assert test_row["addr"] == "0x02e...bde9e"
    assert test_row["total_profit"] == "0"
    assert test_row["avg_accuracy"] == "100.0%"
    assert test_row["avg_stake"] == "1.99"
