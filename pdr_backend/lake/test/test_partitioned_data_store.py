import os
import polars as pl
from pdr_backend.lake.partitioned_data_store import (
    PartitionedDataStore,
)  # Adjust the import based on your project structure


# Initialize the PartitionedDataStore instance for testing
def _get_test_manager(tmpdir):
    partitioned_ds_instance = PartitionedDataStore(str(tmpdir))

    # Fill the table with some data
    example_df = pl.DataFrame(  # pylint: disable=unused-variable
        {
            "timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"],
            "value": [10, 20, 30],
            "address": ["0xasset1", "0xasset1", "0xasset2"],
        }
    )

    dataset_identifier = "test_df"

    view_name = partitioned_ds_instance._generate_view_name(
        partitioned_ds_instance.base_directory + dataset_identifier
    )

    partitioned_ds_instance.duckdb_conn.execute(
        f"CREATE TABLE {view_name} AS SELECT * FROM example_df"
    )

    return [partitioned_ds_instance, dataset_identifier]


def _clean_up_test_manager(tmpdir, dataset_identifier):
    # Clean up the test manager
    dataset_path = os.path.join(str(tmpdir), dataset_identifier)

    persistent_ds_instance = PartitionedDataStore(str(tmpdir))

    view_name = persistent_ds_instance._generate_view_name(dataset_path)

    # Select tables from duckdb
    views = persistent_ds_instance.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    # Drop the view and table
    if view_name in [table[0] for table in views]:
        persistent_ds_instance.duckdb_conn.execute(f"DROP TABLE {view_name}")


def _check_folder_exists(tmpdir, dataset_identifier: str, folder: str):
    dataset_path = os.path.join(str(tmpdir), dataset_identifier, folder)
    folder_status = os.path.exists(dataset_path)
    file_count = len(os.listdir(dataset_path))
    return [folder_status, file_count, dataset_path]


def test_export_data_with_address_hive(
    tmpdir,
):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)
    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="address",
        partition_column="address",
    )

    folder_status, file_count, dataset_path = _check_folder_exists(
        tmpdir, dataset_identifier, "address=0xasset1"
    )
    assert (
        folder_status
    ), f"Parquet Folder was not created as expected. folder: {dataset_path}"
    assert (
        file_count > 0
    ), f"Parquet files was not created as expected. folder: {dataset_path}"

    folder_status, file_count, dataset_path = _check_folder_exists(
        tmpdir, dataset_identifier, "address=0xasset2"
    )
    assert (
        folder_status
    ), f"Parquet Folder was not created as expected. folder: {dataset_path}"
    assert (
        file_count > 0
    ), f"Parquet files was not created as expected. folder: {dataset_path}"

    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_export_data_with_date_hive(
    tmpdir,
):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)
    print("dataset_identifier", dataset_identifier)
    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp",
    )

    folder_status, file_count, dataset_path = _check_folder_exists(
        tmpdir, dataset_identifier, "year=2022/month=1/day=1"
    )
    assert (
        folder_status
    ), f"Parquet Folder was not created as expected. folder: {dataset_path}"
    assert (
        file_count > 0
    ), f"Parquet files was not created as expected. folder: {dataset_path}"

    folder_status, file_count, dataset_path = _check_folder_exists(
        tmpdir, dataset_identifier, "year=2022/month=2/day=1"
    )
    assert (
        folder_status
    ), f"Parquet Folder was not created as expected. folder: {dataset_path}"
    assert (
        file_count > 0
    ), f"Parquet files was not created as expected. folder: {dataset_path}"

    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_create_view_and_query_data(tmpdir):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp",
    )

    query_result = test_manager.create_view_and_query_data(
        dataset_identifier, "SELECT * FROM {view_name} WHERE value > 15"
    )
    assert len(query_result) == 2, "Query did not return the expected number of rows."
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_create_view_and_query_data_without_view_name(tmpdir):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp",
    )

    try:
        test_manager.create_view_and_query_data(
            dataset_identifier, "SELECT * FROM {dataset_path} WHERE value > 15"
        )
    except ValueError as e:
        assert str(e) == "query must contain a {view_name} placeholder"
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_query_data(tmpdir):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp",
    )

    query_result = test_manager.query_data(
        dataset_identifier, "SELECT * FROM {dataset_path} WHERE value > 15"
    )
    assert len(query_result) == 2, "Query did not return the expected number of rows."
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_query_data_without_dataset_path(tmpdir):
    test_manager, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.export_to_parquet(
        dataset_identifier,
        partition_type="date",
        partition_column="timestamp",
    )

    try:
        test_manager.query_data(
            dataset_identifier, "SELECT * FROM {view_name} WHERE value > 15"
        )
    except ValueError as e:
        assert str(e) == "query must contain a {dataset_path} placeholder"
    _clean_up_test_manager(tmpdir, dataset_identifier)
