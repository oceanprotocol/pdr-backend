import os
import polars as pl
from pdr_backend.lake.partitioned_data_store import (
    PartitionedDataStore,
)  # Adjust the import based on your project structure


# Initialize the PartitionedDataStore instance for testing
def _get_test_manager(tmpdir):
    return PartitionedDataStore(str(tmpdir))


def create_and_fill_table(tmpdir):
    test_manager = _get_test_manager(tmpdir)
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
    )
    dataset_identifier = "test_append"
    test_manager.insert_to_table(example_df, dataset_identifier)

    # Check if the view is registered
    view_name = test_manager._generate_view_name(str(tmpdir) + dataset_identifier)
    tables = test_manager.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    assert view_name in [table[0] for table in tables]
    # Since insert_to_table doesn't immediately reflect in the filesystem, this test is limited

def test_finalize_data_with_date_hive(tmpdir):
    test_manager = _get_test_manager(tmpdir)
    dataset_identifier = "test_finalize"
    # 1643673600 is 2022-02-01 00:00:00 in Unix time
    # 1640995200 is 2022-01-01 00:00:00 in Unix time
    # 1640995200 is 2022-03-01 00:00:00 in Unix time
    example_df = pl.DataFrame(
        {"timestamp": [1640995200, 1643673600, 1640995200], "value": [10, 20, 30]}
    )
    test_manager.insert_to_table(example_df, dataset_identifier)
    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp"
    )

    # Check if the files were created
    expected_path = os.path.join(
        str(tmpdir), dataset_identifier, "year=2022", "month=1", "day=1", "data.parquet"
    )
    print("expected_path", expected_path)
    assert os.path.exists(expected_path), "Parquet file was not created as expected."

def test_finalize_data_with_address_hive(tmpdir):
    test_manager = _get_test_manager(tmpdir)
    dataset_identifier = "test_finalize_data_with_address_hive"

    example_df = pl.DataFrame(
        {"address": ['0xasset1', '0xasset1', '0xasset2'], "value": [10, 20, 30]}
    )
    test_manager.insert_to_table(example_df, dataset_identifier)
    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="address",
        partition_column="address"
    )

    # Check if the files were created
    expected_path = os.path.join(
        str(tmpdir), dataset_identifier, "address=0xasset1", "data.parquet"
    )
    print("expected_path", expected_path)
   
def test_create_view_and_query_data(tmpdir):
    test_manager = _get_test_manager(tmpdir)
    dataset_identifier = "test_query"
    # 1643673600 is 2022-02-01 00:00:00 in Unix time
    # 1640995200 is 2022-01-01 00:00:00 in Unix time
    # 1640995200 is 2022-03-01 00:00:00 in Unix time
    example_df = pl.DataFrame(
        {"timestamp": [1640995200, 1643673600, 1640995200], "value": [10, 20, 30]}
    )
    test_manager.insert_to_table(example_df, dataset_identifier)
    test_manager.finalize_data_with_date_hive(dataset_identifier)

    query_result = test_manager.create_view_and_query_data(
        dataset_identifier, "SELECT * FROM {view_name} WHERE value > 15"
    )
    assert len(query_result) == 2, "Query did not return the expected number of rows."

    # Check if the view is registered
    view_name = test_manager._generate_view_name(str(tmpdir) + dataset_identifier)
    tables = test_manager.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    assert view_name in [table[0] for table in tables]
