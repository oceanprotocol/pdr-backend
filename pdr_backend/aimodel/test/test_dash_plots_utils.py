import unittest
import shutil
import os
import pandas as pd
from pdr_backend.aimodel.dash_plots.util import (
    read_files_from_directory,
    filter_file_data_by_date,
)


def tearDown(test_dir):
    # Remove temporary directory and files
    shutil.rmtree(test_dir)


def setUp():
    # Create temporary directory with sample files
    test_dir = "test_files"
    os.makedirs(test_dir, exist_ok=True)
    # Sample Parquet file
    parquet_data = {"timestamp": [4, 5, 6], "close": [40, 50, 60]}
    pd.DataFrame(parquet_data).to_parquet(
        os.path.join(test_dir, "sample.parquet"), index=False
    )
    return test_dir


def test_read_files_from_directory():
    # Call the function to read files
    test_dir = setUp()
    file_data = read_files_from_directory(test_dir)

    # Check if data is read correctly from Parquet file
    assert "sample" in file_data
    assert "close_data" in file_data["sample"]
    assert "timestamps" in file_data["sample"]
    assert list(file_data["sample"]["close_data"]) == [40, 50, 60]
    assert all(
        file_data["sample"]["timestamps"] == pd.to_datetime([4, 5, 6], unit="ms")
    )

    tearDown(test_dir)


def test_filter_file_data_by_date():
    # Sample file data
    file_data = {
        "close_data": [10, 20, 30, 40],
        "timestamps": ["2022-01-01", "2022-01-02", "2022-01-03", "2022-01-04"],
    }

    # Test filtering within date range
    filtered_data = filter_file_data_by_date(file_data, "2022-01-02", "2022-01-03")
    assert filtered_data == {
        "close_data": [20, 30],
        "timestamps": [pd.Timestamp("2022-01-02"), pd.Timestamp("2022-01-03")],
    }

    # Test filtering outside date range
    filtered_data = filter_file_data_by_date(file_data, "2022-01-05", "2022-01-06")
    assert filtered_data == {"close_data": [], "timestamps": []}

    # Test filtering when some timestamps are exactly at the start or end date
    filtered_data = filter_file_data_by_date(file_data, "2022-01-01", "2022-01-02")
    assert filtered_data == {
        "close_data": [10, 20],
        "timestamps": [pd.Timestamp("2022-01-01"), pd.Timestamp("2022-01-02")],
    }

    # Test filtering with invalid input
    # Missing start_date
    with unittest.TestCase().assertRaises(TypeError):
        filter_file_data_by_date(file_data, None, "2022-01-03")
    # Missing end_date
    with unittest.TestCase().assertRaises(TypeError):
        filter_file_data_by_date(file_data, "2022-01-02", None)
