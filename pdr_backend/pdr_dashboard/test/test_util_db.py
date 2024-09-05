from unittest.mock import patch

from enforce_typing import enforce_types
from pdr_backend.lake.subscription import Subscription
from pdr_backend.util.time_types import UnixTimeMs


@enforce_types
@patch("pdr_backend.pdr_dashboard.util.db.DuckDBDataStore")
def test_query_db(
    mock_duckdb_data_store,
    _sample_app,
):
    query = "query"
    db_mgr = _sample_app.data
    db_mgr._query_db(query)

    lake_dir = db_mgr.lake_dir
    mock_duckdb_data_store.assert_called_once_with(lake_dir, read_only=True)
    mock_duckdb_data_store.return_value.query_data.assert_called_once_with(query)


@enforce_types
def test_get_feeds_data(_sample_app):

    db_mgr = _sample_app.data
    result = db_mgr._init_feeds_data()

    assert isinstance(result, list)
    assert len(result) == 20


def test_get_payouts(
    _sample_app,
):
    db_mgr = _sample_app.data

    result = db_mgr.payouts([], [], 1704153000)
    assert len(result) == 2349

    result = db_mgr.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
        1704152700,
    )
    assert isinstance(result, list)
    assert len(result) == 24

    # start date after all payouts should return an empty list
    result = db_mgr.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
        1759154000,
    )
    assert len(result) == 0

    # start date 0 should not filter on start date
    result = db_mgr.payouts(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
        0,
    )
    assert len(result) == 24


def test_get_user_payouts_stats(
    _sample_app,
):
    db_mgr = _sample_app.data
    result = db_mgr._init_predictoor_payouts_stats()

    assert isinstance(result, list)
    assert len(result) == 57

    test_row = [
        row
        for row in result
        if row["user"] == "0x768c5195ea841c544cd09c61650417132615c0b9"
    ][0]

    assert test_row["user"] == "0x768c5195ea841c544cd09c61650417132615c0b9"
    assert test_row["avg_accuracy"] == 39.130434782608695
    assert test_row["avg_stake"] == 2.6666666666666665
    assert test_row["total_profit"] == -36.06628060203039

    # test filtering by start date
    start_date = UnixTimeMs(1721957490000)
    result = db_mgr._init_predictoor_payouts_stats(start_date)

    assert isinstance(result, list)
    assert len(result) == 37


def test_get_feed_daily_subscriptions_by_feed_id(_sample_app):
    db_mgr = _sample_app.data

    feed_id = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"

    result = db_mgr.feed_daily_subscriptions_by_feed_id(feed_id)
    all_subscriptions = db_mgr._query_db(
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

    # test filtering by start date
    start_date = UnixTimeMs(1721957490000)
    result = db_mgr.feed_daily_subscriptions_by_feed_id(feed_id, start_date)
    assert len(result) == 0
