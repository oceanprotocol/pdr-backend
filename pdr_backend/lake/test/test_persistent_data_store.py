import os
import polars as pl
from pdr_backend.lake.persistent_data_store import (
    PersistentDataStore,
)  # Adjust the import based on your project structure


# Initialize the PartitionedDataStore instance for testing
def _get_test_manager(tmpdir):
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
    )
    dataset_identifier = "test_df"

    return [PersistentDataStore(str(tmpdir)), example_df, dataset_identifier]


def _clean_up_test_manager(tmpdir, dataset_identifier):
    # Clean up the test manager
    dataset_path = os.path.join(str(tmpdir), dataset_identifier)

    persistent_ds_instance = PersistentDataStore(str(tmpdir))

    view_name = persistent_ds_instance._generate_view_name(dataset_path)

    # Select tables from duckdb
    views = persistent_ds_instance.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()

    # Drop the view and table
    if view_name in [table[0] for table in views]:
        persistent_ds_instance.duckdb_conn.execute(f"DROP TABLE {view_name}")


def _check_view_exists(tmpdir, test_manager, dataset_identifier):
    view_name = test_manager._generate_view_name(dataset_identifier)
    tables = test_manager.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    return [view_name in [table[0] for table in tables], view_name]


def test_create_and_fill_table(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)

    test_manager._create_and_fill_table(example_df, dataset_identifier)

    # Check if the view is registered
    assert _check_view_exists(tmpdir, test_manager, dataset_identifier)
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_insert_to_exist_table(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)

    test_manager._create_and_fill_table(example_df, dataset_identifier)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(
        tmpdir, test_manager, dataset_identifier
    )
    assert check_result

    # Insert new data to the table
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    test_manager.insert_to_table(example_df, dataset_identifier)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(
        tmpdir, test_manager, dataset_identifier
    )
    assert check_result

    # Check if the new data is inserted
    result = test_manager.duckdb_conn.execute(f"SELECT * FROM {view_name}").fetchall()
    assert len(result) == 6
    print(result)
    assert result[3][0] == "2022-04-01"
    assert result[3][1] == 40
    assert result[4][0] == "2022-05-01"
    assert result[4][1] == 50
    assert result[5][0] == "2022-06-01"
    assert result[5][1] == 60
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_insert_to_new_table(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.insert_to_table(example_df, dataset_identifier)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(
        tmpdir, test_manager, dataset_identifier
    )
    assert check_result

    # Check if the new data is inserted
    result = test_manager.duckdb_conn.execute(f"SELECT * FROM {view_name}").fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_query_data(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)
    test_manager.insert_to_table(example_df, dataset_identifier)

    # Check if the view is registered
    check_result, _ = _check_view_exists(tmpdir, test_manager, dataset_identifier)
    assert check_result

    # Execute the provided SQL query
    result_df = test_manager.query_data(
        dataset_identifier, "SELECT * FROM {view_name} WHERE value > 15"
    )
    assert len(result_df) == 2, "Query did not return the expected number of rows."
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_drop_table(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)

    test_manager.insert_to_table(example_df, dataset_identifier)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(
        tmpdir, test_manager, dataset_identifier
    )
    assert check_result

    # Drop the table
    test_manager.drop_table(dataset_identifier, ds_type="table")

    # Check if the view is dropped
    tables = test_manager.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    assert view_name not in [table[0] for table in tables]
    _clean_up_test_manager(tmpdir, dataset_identifier)


def test_fill_from_csv_destination(tmpdir):
    test_manager, example_df, dataset_identifier = _get_test_manager(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    test_manager.fill_from_csv_destination(csv_folder_path, dataset_identifier)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(
        tmpdir, test_manager, dataset_identifier
    )
    assert check_result

    # Check if the new data is inserted
    result = test_manager.duckdb_conn.execute(f"SELECT * FROM {view_name}").fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30

    _clean_up_test_manager(tmpdir, dataset_identifier)
    # clean csv folder
    # delete files in the folder
    for file in os.listdir(csv_folder_path):
        file_path = os.path.join(csv_folder_path, file)
        os.remove(file_path)

    # delete the folder
    os.rmdir(csv_folder_path)
