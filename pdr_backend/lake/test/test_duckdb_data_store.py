#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import threading
import time

import duckdb
import polars as pl

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import Table, TempTable


# Initialize the DuckDBDataStore instance for testing
def _setup_fixture(tmpdir):
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
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
