from unittest.mock import patch

from enforce_typing import enforce_types
from pdr_backend.pdr_dashboard.util.db import DBGetter
from pdr_backend.pdr_dashboard.test.resources import (
    _prepare_test_db,
    _clear_test_db,
)
from pdr_backend.lake.prediction import Prediction
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.subscription import Subscription


@enforce_types
@patch("pdr_backend.pdr_dashboard.util.db.DuckDBDataStore")
def test_query_db(
    mock_duckdb_data_store,
):
    lake_dir = "lake_dir"
    query = "query"
    db_getter = DBGetter(lake_dir)
    db_getter._query_db(query)
    mock_duckdb_data_store.assert_called_once_with(lake_dir, read_only=True)
    mock_duckdb_data_store.return_value.query_data.assert_called_once_with(query)


@enforce_types
def test_get_feeds_data(
    tmpdir,
    _sample_first_predictions,
):
    ppss, sample_data_df = _prepare_test_db(
        tmpdir, _sample_first_predictions, Prediction.get_lake_table_name()
    )

    db_getter = DBGetter(ppss.lake_ss.lake_dir)
    result = db_getter.feeds_data()

    assert isinstance(result, list)
    assert len(result) == len(sample_data_df)

    _clear_test_db(ppss.lake_ss.lake_dir)


@enforce_types
def test_get_payouts(
    tmpdir,
    _sample_payouts,
):
    ppss, _ = _prepare_test_db(
        tmpdir, _sample_payouts, table_name=Payout.get_lake_table_name()
    )

    db_getter = DBGetter(ppss.lake_ss.lake_dir)
    result = db_getter.payouts([], [], 1704153000)
    assert len(result) == 4

    result = db_getter.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        1704152700,
    )
    assert isinstance(result, list)
    assert len(result) == 2

    # start date after all payouts should return an empty list
    result = db_getter.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        1704154000,
    )
    assert len(result) == 0

    # start date 0 should not filter on start date
    result = db_getter.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"],
        0,
    )
    assert len(result) == 2

    _clear_test_db(ppss.lake_ss.lake_dir)


def test_get_feed_daily_subscriptions_by_feed_id(tmpdir, _sample_subscriptions):
    ppss, _ = _prepare_test_db(
        tmpdir, _sample_subscriptions, table_name=Subscription.get_lake_table_name()
    )

    feed_id = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"

    db_getter = DBGetter(ppss.lake_ss.lake_dir)
    result = db_getter.feed_daily_subscriptions_by_feed_id(feed_id)
    all_subscriptions = db_getter._query_db(
        f"SELECT * FROM {Subscription.get_lake_table_name()}"
    )

    # Verify the response type and length
    assert isinstance(result, list)
    assert len(result) == 1

    # Filter subscriptions from the given contract
    subscriptions_from_given_contract = [
        item for item in all_subscriptions if feed_id in item["ID"]
    ]

    # Verify the fields in the result
    assert result[0]["day"] is not None, "Day field should not be None"
    assert result[0]["count"] == len(
        subscriptions_from_given_contract
    ), "Count should match the number of subscriptions from the given contract"
    assert result[0]["revenue"] == sum(
        obj["last_price_value"] for obj in subscriptions_from_given_contract
    ), "Revenue should be the sum of last_price_value of the subscriptions"
