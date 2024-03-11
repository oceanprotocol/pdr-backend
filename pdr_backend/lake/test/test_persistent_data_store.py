import os
import polars as pl
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.test.conftest import _clean_up_persistent_data_store


# Initialize the PersistentDataStore instance for testing
def _get_persistent_data_store(tmpdir):
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
    )
    table_name = "test_df"

    return [PersistentDataStore(str(tmpdir)), example_df, table_name]


def _check_view_exists(persistent_data_store, table_name):
    tables = persistent_data_store.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    return [table_name in [table[0] for table in tables], table_name]


def test_create_and_fill_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store._create_and_fill_table(example_df, table_name)

    # Check if the view is registered
    assert _check_view_exists(persistent_data_store, table_name)
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_insert_to_exist_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store._create_and_fill_table(example_df, table_name)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(persistent_data_store, table_name)
    assert check_result

    # Insert new data to the table
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(persistent_data_store, table_name)
    assert check_result

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {view_name}"
    ).fetchall()
    assert len(result) == 6
    print(result)
    assert result[3][0] == "2022-04-01"
    assert result[3][1] == 40
    assert result[4][0] == "2022-05-01"
    assert result[4][1] == 50
    assert result[5][0] == "2022-06-01"
    assert result[5][1] == 60
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_insert_to_new_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(persistent_data_store, table_name)
    assert check_result

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {view_name}"
    ).fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_query_data(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)
    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the view is registered
    check_result, _ = _check_view_exists(persistent_data_store, table_name)
    assert check_result

    # Execute the provided SQL query
    result_df = persistent_data_store.query_data(
        f"SELECT * FROM {table_name} WHERE value > 15"
    )
    assert len(result_df) == 2, "Query did not return the expected number of rows."
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_drop_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(persistent_data_store, table_name)
    assert check_result

    # Drop the table
    persistent_data_store.drop_table(table_name, ds_type="table")

    # Check if the view is dropped
    tables = persistent_data_store.duckdb_conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
    ).fetchall()
    assert view_name not in [table[0] for table in tables]
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_fill_from_csv_destination(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    persistent_data_store.fill_from_csv_destination(csv_folder_path, table_name)

    # Check if the view is registered
    check_result, view_name = _check_view_exists(persistent_data_store, table_name)

    assert check_result

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {view_name}"
    ).fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30

    _clean_up_persistent_data_store(tmpdir, table_name)
    # clean csv folder
    # delete files in the folder
    for file in os.listdir(csv_folder_path):
        file_path = os.path.join(csv_folder_path, file)
        os.remove(file_path)

    # delete the folder
    os.rmdir(csv_folder_path)
