import os
import threading
import time
from unittest.mock import patch, MagicMock

import duckdb
import polars as pl

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import Table, TempTable
from pdr_backend.util.time_types import UnixTimeS


# Initialize the DuckDBDataStore instance for testing
def _setup_fixture(tmpdir, df=None):
    example_df = df
    if example_df is None:
        example_df = pl.DataFrame(
            {
                "timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"],
                "value": [10, 20, 30],
            }
        )
    table_name = "test_df"

    return [DuckDBDataStore(str(tmpdir)), example_df, table_name]


def test_insert(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.create_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists


def test_insert_to_exist_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.create_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Insert new data to the table
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    db.insert_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(f"SELECT * FROM {table_name}").fetchall()
    assert len(result) == 6
    assert result[3][0] == "2022-04-01"
    assert result[3][1] == 40
    assert result[4][0] == "2022-05-01"
    assert result[4][1] == 50
    assert result[5][0] == "2022-06-01"
    assert result[5][1] == 60


def test_insert_to_new_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.insert_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(f"SELECT * FROM {table_name}").fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30


def test_query(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    db.insert_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Execute the provided SQL query
    result_df = db.query_data(f"SELECT * FROM {table_name} WHERE value > 15")
    assert len(result_df) == 2, "Query did not return the expected number of rows."


def test_drop_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.insert_from_df(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Drop the table
    db.drop_table(table_name)

    # Check if the table is dropped
    table_names = db.get_table_names()
    assert table_name not in table_names


def test_insert_from_csv(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    db.insert_from_csv(table_name, csv_folder_path)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(f"SELECT * FROM {table_name}").fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30

    # clean csv folder
    # delete files in the folder
    for file in os.listdir(csv_folder_path):
        file_path = os.path.join(csv_folder_path, file)
        os.remove(file_path)

    # delete the folder
    os.rmdir(csv_folder_path)


def test_multiton_instances(tmpdir):
    duckdb_1 = DuckDBDataStore(str(tmpdir))
    duckdb_2 = DuckDBDataStore(str(tmpdir))

    assert id(duckdb_1) == id(duckdb_2)


def test_clear_instances(tmpdir):
    duckdb_1 = DuckDBDataStore(str(tmpdir))
    DuckDBDataStore.clear_instances()
    duckdb_2 = DuckDBDataStore(str(tmpdir))

    assert id(duckdb_1) != id(duckdb_2)


def test_clear_instances_with_multiple_instances(tmpdir):
    duckdb_1 = DuckDBDataStore(str(tmpdir))
    duckdb_2 = DuckDBDataStore(str(tmpdir))
    DuckDBDataStore.clear_instances()
    duckdb_3 = DuckDBDataStore(str(tmpdir))
    duckdb_4 = DuckDBDataStore(str(tmpdir))

    assert id(duckdb_1) != id(duckdb_3)
    assert id(duckdb_2) != id(duckdb_3)
    assert id(duckdb_1) != id(duckdb_4)
    assert id(duckdb_2) != id(duckdb_4)
    assert id(duckdb_3) == id(duckdb_4)


def test_multiton_instances_with_different_base_paths(tmpdir):
    duckdb_1 = DuckDBDataStore(str(tmpdir))

    different_path = str(tmpdir) + "/1"
    os.makedirs(different_path, exist_ok=True)
    duckdb_2 = DuckDBDataStore(different_path)

    assert id(duckdb_1) != id(duckdb_2)


def test__duckdb_connection(tmpdir):
    """
    Test datastore.
    """
    assert isinstance(
        DuckDBDataStore(str(tmpdir)).duckdb_conn, duckdb.DuckDBPyConnection
    ), "The connection is not a DuckDBPyConnection"


def test_move_table_data(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    db.insert_from_df(example_df, TempTable(table_name).table_name)

    # Check if the table is registered
    table_exists = db.table_exists(TempTable(table_name).table_name)
    assert table_exists

    # Move the table
    table = Table(table_name)
    db.move_table_data(TempTable(table_name), table)

    # Assert table hasn't dropped
    table_names = db.get_table_names()
    assert TempTable(table_name).table_name in table_names

    # Drop interim TEMP table
    db.drop_table(TempTable(table_name).table_name)

    # Assert temp table is dropped
    table_names = db.get_table_names()
    assert TempTable(table_name).table_name not in table_names

    # Check if the new table is created
    assert table_name in table_names

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(f"SELECT * FROM {table_name}").fetchall()

    assert len(result) == 3
    assert result[0][0] == "2022-01-01"


def test_etl_view(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    db.insert_from_df(example_df, Table(table_name).table_name)

    other_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    db.insert_from_df(other_df, TempTable(table_name).table_name)

    # Assemble view query and create the view
    view_name = "_update"
    view_query = """
    CREATE VIEW {} AS
    (
        SELECT * FROM {}
        UNION ALL
        SELECT * FROM {}
    )""".format(
        view_name,
        Table(table_name).table_name,
        TempTable(table_name).table_name,
    )
    db.query_data(view_query)

    # Assert number of views is equal to 1
    view_names = db.get_view_names()
    assert len(view_names) == 1

    # Assert view is registered
    check_result = db.view_exists(view_name)
    assert check_result

    # Assert view returns the correct, min(timestamp)
    result = db.duckdb_conn.execute(
        f"SELECT min(timestamp) FROM {view_name}"
    ).fetchall()
    assert result[0][0] == "2022-01-01"

    # Assert view returns the correct, max(timestamp)
    result = db.duckdb_conn.execute(
        f"SELECT max(timestamp) FROM {view_name}"
    ).fetchall()
    assert result[0][0] == "2022-06-01"


def thread_with_return_value(db, table_name):
    result = db.query_data(f"SELECT * FROM {table_name}")
    return result


def test_multiple_thread_table_updates(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    # Check that table is empty by default
    result = db.query_data(f"SELECT * FROM {table_name}")
    assert result is None

    thread_result = []
    thread1 = threading.Thread(
        target=thread_function_write_to_db, args=(csv_folder_path, tmpdir)
    )
    thread2 = threading.Thread(
        target=thread_function_read_from_db,
        args=(csv_folder_path, tmpdir, thread_result),
    )
    thread1.start()
    thread2.start()

    time.sleep(2)

    assert thread_result[0] is not None
    assert len(thread_result[0]) == 3
    assert thread_result[0]["timestamp"][0] == "2022-01-01"
    assert thread_result[0]["value"][0] == 10
    assert thread_result[0]["timestamp"][1] == "2022-02-01"
    assert thread_result[0]["value"][1] == 20
    assert thread_result[0]["timestamp"][2] == "2022-03-01"
    assert thread_result[0]["value"][2] == 30


def thread_function_write_to_db(csv_folder_path, tmpdir):
    db, _, table_name = _setup_fixture(tmpdir)
    db.insert_from_csv(table_name, csv_folder_path)


def thread_function_read_from_db(csv_folder_path, tmpdir, thread_result):
    db, _, table_name = _setup_fixture(tmpdir)

    # Wait for the first thread to finish
    time.sleep(1)
    # Check if the new data is inserted
    thread_result.append(db.query_data(f"SELECT * FROM {table_name}"))

    # clean csv folder
    # delete files in the folder
    for file in os.listdir(csv_folder_path):
        file_path = os.path.join(csv_folder_path, file)
        os.remove(file_path)

    # delete the folder
    os.rmdir(csv_folder_path)


def test_create_table(tmpdir):
    """
    Test create table if not exists.
    """
    db, example_df, table_name = _setup_fixture(tmpdir)

    example_df_schema = example_df.schema
    # Create table
    db.create_empty(table_name, example_df_schema)

    # Check if the table is registered
    check_result = db.table_exists(table_name)
    assert check_result


def test_should_export(tmpdir):
    db, _, _ = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "test_table")
    os.makedirs(table_folder_path, exist_ok=True)

    # Create a test case where max timestamp from parquet files is in the past
    seconds_between_exports = UnixTimeS(600)  # 10 minutes
    current_timestamp = UnixTimeS(int(time.time())).to_milliseconds()

    # Mock _get_max_timestamp_from_parquet_files to return a timestamp 15 minutes ago
    db._get_max_timestamp_from_parquet_files = (
        lambda path: current_timestamp - 15 * 60 * 1000
    )

    assert db._should_export(table_folder_path, seconds_between_exports) is True

    # Now mock it to return a more recent timestamp, within the export window
    db._get_max_timestamp_from_parquet_files = (
        lambda path: current_timestamp - 5 * 60 * 1000
    )

    assert db._should_export(table_folder_path, seconds_between_exports) is False


@patch("pdr_backend.lake.duckdb_data_store.duckdb.execute")
def test_get_max_timestamp_from_parquet_files(mock_duckdb_execute, tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "exports")
    os.makedirs(table_folder_path, exist_ok=True)

    # Simulate the existence of a Parquet file with a max timestamp
    parquet_file = os.path.join(table_folder_path, f"{table_name}_1640995200.parquet")
    example_df.write_parquet(parquet_file)

    # Mock DuckDB to return a known max timestamp
    mock_duckdb_execute.return_value.fetchone.return_value = (1640995200,)

    max_timestamp = db._get_max_timestamp_from_parquet_files(table_folder_path)
    assert max_timestamp == 1640995200

    # Simulate no Parquet files
    db._get_max_timestamp_from_parquet_files = lambda path: 0
    assert db._get_max_timestamp_from_parquet_files(table_folder_path) == 0


@patch("pdr_backend.lake.duckdb_data_store.DuckDBDataStore.query_scalar")
def test_export_table_to_parquet(mock_query_scalar, tmpdir):
    # read the pdr_payouts.csv file in the same folder
    df = pl.read_csv("pdr_backend/lake/test/pdr_payouts.csv")
    db, example_df, table_name = _setup_fixture(tmpdir, df)
    table_folder_path = os.path.join(str(tmpdir), "test_table")
    os.makedirs(table_folder_path, exist_ok=True)

    # Mocking _get_max_timestamp_from_parquet_files to return 0 (i.e., no previous export)
    db._get_max_timestamp_from_parquet_files = lambda path: 0

    # Insert example data into DuckDB table
    db.create_from_df(example_df, table_name)

    mock_query_scalar.return_value = 1640995200
    # Export the table to Parquet
    db._export_table_to_parquet(table_name, table_folder_path)

    # Check if the Parquet file is created
    files = os.listdir(table_folder_path)
    assert any(file.endswith(".parquet") for file in files), "No Parquet file created"


def test_should_nuke_table_folders_and_re_export_db_bronze(tmpdir):
    db, _, _ = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "bronze_table")
    os.makedirs(table_folder_path, exist_ok=True)
    with open(f"{table_folder_path}/table.parquet", "a"):
        pass

    # Test when "bronze" is in the table_name
    result = db._should_nuke_table_folders_and_re_export_db(
        table_folder_path, 5, "bronze_table", 0
    )
    assert result is True, "Failed to nuke bronze table folders"


def test_should_nuke_table_folders_and_re_export_db_non_bronze_exceed_file_limit(
    tmpdir,
):
    db, _, _ = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "test_table")
    os.makedirs(table_folder_path, exist_ok=True)

    # Create dummy files
    for i in range(10):
        with open(os.path.join(table_folder_path, f"file_{i}.parquet"), "w"):
            pass

    # Test when the number of files exceeds the limit
    result = db._should_nuke_table_folders_and_re_export_db(
        table_folder_path, 5, "test_table", 20
    )
    assert result is True, "Failed to detect exceeding file limit"


def test_should_nuke_table_folders_and_re_export_db_non_bronze_below_file_limit(tmpdir):
    db, _, _ = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "test_table")
    os.makedirs(table_folder_path, exist_ok=True)

    # Create dummy files
    for i in range(3):
        with open(os.path.join(table_folder_path, f"file_{i}.parquet"), "w"):
            pass

    # Test when the number of files is below the limit
    result = db._should_nuke_table_folders_and_re_export_db(
        table_folder_path, 5, "test_table", 20
    )
    assert result is False, "Incorrectly detected nuke requirement for non-bronze table"


@patch("pdr_backend.lake.duckdb_data_store.delete_folder")
def test_nuke_table_folders_and_re_export_db(mock_delete_folder, tmpdir):
    db, _, _ = _setup_fixture(tmpdir)
    table_folder_path = os.path.join(str(tmpdir), "test_table")
    os.makedirs(table_folder_path, exist_ok=True)

    # Simulate deleting the files by mocking `delete_folder`
    db._nuke_table_folders(table_folder_path)

    # Ensure delete_folder was called with the correct folder path
    mock_delete_folder.assert_called_once_with(table_folder_path)


@patch("pdr_backend.lake.duckdb_data_store.DuckDBDataStore._should_export")
@patch("pdr_backend.lake.duckdb_data_store.DuckDBDataStore._export_table_to_parquet")
@patch("pdr_backend.lake.duckdb_data_store.DuckDBDataStore._nuke_table_folders")
@patch(
    "pdr_backend.lake.duckdb_data_store.DuckDBDataStore._should_nuke_table_folders_and_re_export_db"
)
@patch("pdr_backend.lake.duckdb_data_store.get_export_folder_path")
def test_export_tables_to_parquet_files(
    mock_get_export_folder_path,
    mock_should_nuke_table_folders,
    mock_nuke_table_folders,
    mock_should_export,
    mock_export_table_to_parquet,
    tmpdir,
):
    db, _, _ = _setup_fixture(tmpdir)

    # Mock return values for internal methods
    mock_get_export_folder_path.return_value = os.path.join(str(tmpdir), "exports")
    mock_should_nuke_table_folders.return_value = False  # Simulate no nuke
    mock_should_export.return_value = True  # Simulate exporting is needed

    # Simulate tables in the database
    db.query_data = MagicMock(return_value={"name": ["table1", "table2"]})

    # Call the method
    db.export_tables_to_parquet_files(
        seconds_between_exports=UnixTimeS(600),
        number_of_files_after_which_re_export_db=5,
    )

    # Check that _should_nuke_table_folders_and_re_export_db was called for each table
    assert mock_should_nuke_table_folders.call_count == 2

    # Ensure _export_table_to_parquet was called for each table
    assert mock_export_table_to_parquet.call_count == 2

    # Ensure _nuke_table_folders was not called since nuke condition is False
    mock_nuke_table_folders.assert_not_called()

    # Ensure _should_export was called for each table
    assert mock_should_export.call_count == 2
