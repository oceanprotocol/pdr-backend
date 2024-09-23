from unittest.mock import patch

import time
import pandas
from enforce_typing import enforce_types

from pdr_backend.lake.subscription import Subscription
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.duckdb_data_store import tbl_parquet_path

# Define necessary global variables for the tests
test_query = "SELECT * FROM test_table"
cache_file_name = "test_query"


@enforce_types
@patch("pdr_backend.pdr_dashboard.util.duckdb_file_reader.duckdb.execute")
def test_query_db(mock_duckdb_execute, _sample_app):
    db_mgr = _sample_app.data
    db_mgr.file_reader._query_db(test_query)

    # Assert that duckdb.execute was called once with the correct query
    mock_duckdb_execute.assert_called_once_with(test_query)

    # Mocking the return value from duckdb.execute(query)
    mock_duckdb_execute.return_value.pl.assert_called_once()


@enforce_types
def test_get_feeds_data(_sample_app):

    db_mgr = _sample_app.data
    result = db_mgr._init_feeds_data()

    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 20


def test_get_payouts(
    _sample_app,
):
    db_mgr = _sample_app.data

    db_mgr.start_date = UnixTimeMs(1704152700000).to_dt()
    db_mgr.file_reader.start_date = UnixTimeMs(1704152700000).to_dt()
    result = db_mgr.payouts_from_bronze_predictions([], [])
    assert len(result) == 2369

    db_mgr.start_date = UnixTimeMs(1721952002000).to_dt()
    db_mgr.file_reader.start_date = UnixTimeMs(1721952002000).to_dt()
    result = db_mgr.payouts_from_bronze_predictions(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
    )
    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 24

    # start date after all payouts should return an empty list
    db_mgr.start_date = UnixTimeMs(1759154000000).to_dt()
    db_mgr.file_reader.start_date = UnixTimeMs(1759154000000).to_dt()
    result = db_mgr.payouts_from_bronze_predictions(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
    )
    assert len(result) == 0

    # start date 0 should not filter on start date
    db_mgr.start_date = 0
    db_mgr.file_reader.start_date = 0
    result = db_mgr.payouts_from_bronze_predictions(
        ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"],
        ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"],
    )
    assert len(result) == 24


def test_get_user_payouts_stats(
    _sample_app,
):
    db_mgr = _sample_app.data
    result = db_mgr._init_predictoor_payouts_stats()

    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 57

    test_row = result[
        result["user"] == "0x768c5195ea841c544cd09c61650417132615c0b9"
    ].to_dict(orient="records")[0]

    assert test_row["user"] == "0x768c5195ea841c544cd09c61650417132615c0b9"
    assert test_row["avg_accuracy"] == 36.231884057971016
    assert test_row["avg_stake"] == 2.318840579710145
    assert test_row["total_profit"] == -24.045497962220715

    # test filtering by start date
    db_mgr.start_date = UnixTimeMs(1721957490000).to_dt()
    db_mgr.file_reader.start_date = UnixTimeMs(1721957490000).to_dt()
    result = db_mgr._init_predictoor_payouts_stats()

    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 37


def test_get_feed_daily_subscriptions_by_feed_id(_sample_app):
    db_mgr = _sample_app.data

    feed_id = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"

    result = db_mgr.feed_daily_subscriptions_by_feed_id(feed_id)
    all_subscriptions = db_mgr.file_reader._query_db(
        f"SELECT * FROM {tbl_parquet_path(db_mgr.lake_dir, Subscription)}"
    )

    # Verify the response type and length
    assert isinstance(result, pandas.DataFrame)
    assert len(result) == 1

    result = result.to_dict(orient="records")
    all_subscriptions = all_subscriptions.to_dict(orient="records")

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
    db_mgr.start_date = UnixTimeMs(1721957490000).to_dt()
    result = db_mgr.feed_daily_subscriptions_by_feed_id(feed_id)
    assert len(result) == 0


@patch("os.makedirs")
@patch("os.path.exists")
@patch("os.path.getmtime")
@patch("duckdb.execute")
def test_cache_exists_recent_file(
    mock_duckdb_execute, mock_getmtime, mock_exists, _mock_makedirs, _sample_app
):
    """
    Test when cache file exists and is less than 1 hour old.
    """
    db_mgr = _sample_app.data
    mock_exists.return_value = True  # Simulate that the cache file exists
    mock_getmtime.return_value = (
        time.time() - 1000
    )  # Cache file is 1000 seconds old (< 1 hour)

    mock_duckdb_execute.return_value.fetchone.return_value = (42,)

    # Call the function
    result = db_mgr.file_reader._check_cache_query_data(
        test_query, cache_file_name, scalar=True
    )

    # Check that no new query was executed, and cached data was used
    mock_duckdb_execute.assert_called_with(
        f"SELECT * FROM '{db_mgr.lake_dir}/exports/cache/test_query.parquet'"
    )
    assert result == 42


@patch("os.makedirs")
@patch("os.path.exists")
@patch("duckdb.execute")
def test_cache_does_not_exist(
    mock_duckdb_execute, mock_exists, _mock_makedirs, _sample_app
):
    """
    Test when cache file does not exist, so query is executed and cached.
    """
    db_mgr = _sample_app.data
    mock_exists.return_value = False  # Simulate that the cache file does not exist
    mock_duckdb_execute.return_value.fetchone.return_value = (55,)

    # Call the function
    result = db_mgr.file_reader._check_cache_query_data(
        test_query, cache_file_name, scalar=True
    )

    file_path = f"{db_mgr.lake_dir}/exports/cache/test_query.parquet"
    # Check that the query was executed and cached
    mock_duckdb_execute.assert_any_call(
        f"COPY ({test_query}) TO '{file_path}' (FORMAT 'parquet')"
    )
    assert result == 55


@patch("os.makedirs")
@patch("os.path.exists")
@patch("duckdb.execute")
def test_non_scalar_query(
    mock_duckdb_execute, mock_exists, _mock_makedirs, _sample_app
):
    """
    Test non-scalar queries return a DataFrame.
    """
    db_mgr = _sample_app.data
    mock_exists.return_value = False  # Simulate that the cache file does not exist
    mock_df = pandas.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    mock_duckdb_execute.return_value.pl.return_value.to_pandas.return_value = mock_df

    # Call the function
    result = db_mgr.file_reader._check_cache_query_data(
        test_query, cache_file_name, scalar=False
    )

    # Check that the result is returned as a pandas DataFrame
    assert isinstance(result, pandas.DataFrame)
    assert mock_duckdb_execute.called


@patch("os.makedirs")
@patch("os.path.exists")
@patch("os.path.getmtime")
@patch("duckdb.execute")
def test_cache_not_used_for_scalar(
    mock_duckdb_execute, mock_getmtime, mock_exists, _mock_makedirs, _sample_app
):
    """
    Test when cache exists but scalar data is requested and cache is not used.
    """
    db_mgr = _sample_app.data
    mock_exists.return_value = True  # Cache exists
    mock_getmtime.return_value = time.time() - 1000  # File is < 1 hour old
    mock_duckdb_execute.return_value.fetchone.return_value = (10,)

    scalar_query = "SELECT count(*) FROM test_table"
    # Call the function
    result = db_mgr.file_reader._check_cache_query_data(
        scalar_query, cache_file_name, scalar=True
    )

    # Check if scalar result is returned
    assert result == 10
