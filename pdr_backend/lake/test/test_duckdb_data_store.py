import os
import threading
import time

import duckdb
import polars as pl

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import ETLTable, NamedTable, TempTable


# Initialize the DuckDBDataStore instance for testing
def _setup_fixture(tmpdir):
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
    )
    table_name = "test_df"

    return [DuckDBDataStore(str(tmpdir)), example_df, table_name]


def test_create_and_fill_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db._create_and_fill_table(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists


def test_insert_to_exist_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db._create_and_fill_table(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Insert new data to the table
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    db.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(
        f"SELECT * FROM {table_name} ORDER BY timestamp"
    ).fetchall()

    assert len(result) == 6
    assert result[3][0] == "2022-04-01"
    assert result[3][1] == 40
    assert result[4][0] == "2022-05-01"
    assert result[4][1] == 50
    assert result[5][0] == "2022-06-01"
    assert result[5][1] == 60


def test_insert_to_new_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.insert_to_table(example_df, table_name)

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
    db.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Execute the provided SQL query
    result_df = db.query_data(f"SELECT * FROM {table_name} WHERE value > 15")
    assert len(result_df) == 2, "Query did not return the expected number of rows."


def test_drop_table(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)

    db.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = db.table_exists(table_name)
    assert table_exists

    # Drop the table
    db.drop_table(table_name)

    # Check if the table is dropped
    table_names = db.get_table_names()
    assert table_name not in table_names


def test_fill_table_from_csv(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    db.fill_table_from_csv(table_name, csv_folder_path)

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
    db.insert_to_table(example_df, TempTable(table_name).fullname)

    # Check if the table is registered
    table_exists = db.table_exists(TempTable(table_name).fullname)
    assert table_exists

    # Move the table
    table = NamedTable(table_name)
    db.move_table_data(TempTable(table_name), table)

    # Assert table hasn't dropped
    table_names = db.get_table_names()
    assert TempTable(table_name).fullname in table_names

    # Drop interim TEMP table
    db.drop_table(TempTable(table_name).fullname)

    # Assert temp table is dropped
    table_names = db.get_table_names()
    assert TempTable(table_name).fullname not in table_names

    # Check if the new table is created
    assert table_name in table_names

    # Check if the new data is inserted
    result = db.duckdb_conn.execute(f"SELECT * FROM {table_name}").fetchall()

    assert len(result) == 3
    assert result[0][0] == "2022-01-01"


def test_etl_view(tmpdir):
    db, example_df, table_name = _setup_fixture(tmpdir)
    db.insert_to_table(example_df, NamedTable(table_name).fullname)

    other_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    db.insert_to_table(other_df, TempTable(table_name).fullname)

    # Assemble view query and create the view
    view_name = ETLTable(table_name).fullname
    view_query = """
    CREATE VIEW {} AS
    (
        SELECT * FROM {}
        UNION ALL
        SELECT * FROM {}
    )""".format(
        ETLTable(table_name).fullname,
        NamedTable(table_name).fullname,
        TempTable(table_name).fullname,
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
    db.fill_table_from_csv(table_name, csv_folder_path)


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


def test_create_table_if_not_exists(tmpdir):
    """
    Test create table if not exists.
    """
    db, example_df, table_name = _setup_fixture(tmpdir)

    example_df_schema = example_df.schema
    # Create table
    db.create_table_if_not_exists(table_name, example_df_schema)

    # Check if the table is registered
    check_result = db.table_exists(table_name)
    assert check_result


def test_duplicate_rows(tmpdir):
    """
    Test duplicate rows.
    """
    db, example_df, table_name = _setup_fixture(tmpdir)
    db.insert_to_table(example_df, table_name)
    db.insert_to_table(example_df, table_name)

    rows = db.query_data(f"SELECT * FROM {table_name}")
    assert len(rows) == len(example_df)

    # one row is common to the OG example df => should be discarded
    # one has same timestamp but changed value => should be inserted
    # one is completely new => should be inserted
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-03-01", "2022-06-01"], "value": [50, 30, 60]}
    )

    db.insert_to_table(example_df, table_name)
    rows = db.query_data(f"SELECT * FROM {table_name}")
    assert len(rows) == len(example_df) + 2
