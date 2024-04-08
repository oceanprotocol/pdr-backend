import os
import polars as pl
import duckdb

from pdr_backend.lake.table import TableType, get_table_name
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.test.conftest import _clean_up_persistent_data_store
from pdr_backend.lake.csv_data_store import CSVDataStore


# Initialize the PersistentDataStore instance for testing
def _get_persistent_data_store(tmpdir):
    example_df = pl.DataFrame(
        {"timestamp": ["2022-01-01", "2022-02-01", "2022-03-01"], "value": [10, 20, 30]}
    )
    table_name = "test_df"

    return [PersistentDataStore(str(tmpdir)), example_df, table_name]


def test_create_and_fill_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store._create_and_fill_table(example_df, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_insert_to_exist_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store._create_and_fill_table(example_df, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Insert new data to the table
    example_df = pl.DataFrame(
        {"timestamp": ["2022-04-01", "2022-05-01", "2022-06-01"], "value": [40, 50, 60]}
    )
    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {table_name}"
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

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {table_name}"
    ).fetchall()
    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
    assert result[0][1] == 10
    assert result[1][0] == "2022-02-01"
    assert result[1][1] == 20
    assert result[2][0] == "2022-03-01"
    assert result[2][1] == 30
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_query(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)
    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Execute the provided SQL query
    result_df = persistent_data_store.query_data(
        f"SELECT * FROM {table_name} WHERE value > 15"
    )
    assert len(result_df) == 2, "Query did not return the expected number of rows."
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_drop_table(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)

    persistent_data_store.insert_to_table(example_df, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Drop the table
    persistent_data_store.drop_table(table_name)

    # Check if the table is dropped
    table_names = persistent_data_store.get_table_names()
    assert table_name not in table_names
    _clean_up_persistent_data_store(tmpdir, table_name)


def test_fill_from_csv_destination(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)
    csv_folder_path = os.path.join(str(tmpdir), "csv_folder")
    os.makedirs(csv_folder_path, exist_ok=True)
    example_df.write_csv(os.path.join(str(csv_folder_path), "data.csv"))

    persistent_data_store.fill_from_csv_destination(csv_folder_path, table_name)

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(table_name)
    assert table_exists

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {table_name}"
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


def test_multiton_instances(tmpdir):
    persistent_data_store_1 = PersistentDataStore(str(tmpdir))
    persistent_data_store_2 = PersistentDataStore(str(tmpdir))

    assert id(persistent_data_store_1) == id(persistent_data_store_2)

    _clean_up_persistent_data_store(tmpdir)


def test_clear_instances(tmpdir):
    persistent_data_store_1 = PersistentDataStore(str(tmpdir))
    PersistentDataStore.clear_instances()
    persistent_data_store_2 = PersistentDataStore(str(tmpdir))

    assert id(persistent_data_store_1) != id(persistent_data_store_2)

    _clean_up_persistent_data_store(tmpdir)


def test_clear_instances_with_multiple_instances(tmpdir):
    persistent_data_store_1 = PersistentDataStore(str(tmpdir))
    persistent_data_store_2 = PersistentDataStore(str(tmpdir))
    PersistentDataStore.clear_instances()
    persistent_data_store_3 = PersistentDataStore(str(tmpdir))
    persistent_data_store_4 = PersistentDataStore(str(tmpdir))

    assert id(persistent_data_store_1) != id(persistent_data_store_3)
    assert id(persistent_data_store_2) != id(persistent_data_store_3)
    assert id(persistent_data_store_1) != id(persistent_data_store_4)
    assert id(persistent_data_store_2) != id(persistent_data_store_4)
    assert id(persistent_data_store_3) == id(persistent_data_store_4)

    _clean_up_persistent_data_store(tmpdir)


def test_multiton_instances_with_different_base_paths(tmpdir):
    persistent_data_store_1 = PersistentDataStore(str(tmpdir))

    different_path = str(tmpdir) + "/1"
    os.makedirs(different_path, exist_ok=True)
    persistent_data_store_2 = PersistentDataStore(different_path)

    assert id(persistent_data_store_1) != id(persistent_data_store_2)

    _clean_up_persistent_data_store(tmpdir)
    _clean_up_persistent_data_store(different_path)


def test_multiton_with_CSVDataStore(tmpdir):
    persistent_data_store_1 = PersistentDataStore(str(tmpdir))
    csv_data_store_1 = CSVDataStore(str(tmpdir))

    assert id(persistent_data_store_1) != id(csv_data_store_1)

    # test cls._instances so that it is not the same
    assert persistent_data_store_1._instances != csv_data_store_1._instances

    _clean_up_persistent_data_store(tmpdir)


def test__duckdb_connection(tmpdir):
    """
    Test datastore.
    """
    assert isinstance(
        PersistentDataStore(str(tmpdir)).duckdb_conn, duckdb.DuckDBPyConnection
    ), "The connection is not a DuckDBPyConnection"

    _clean_up_persistent_data_store(tmpdir)


def test_move_table_data(tmpdir):
    persistent_data_store, example_df, table_name = _get_persistent_data_store(tmpdir)
    persistent_data_store.insert_to_table(
        example_df, get_table_name(table_name, TableType.TEMP)
    )

    # Check if the table is registered
    table_exists = persistent_data_store.table_exists(
        get_table_name(table_name, TableType.TEMP)
    )
    assert table_exists

    # Move the table
    persistent_data_store.move_table_data(
        get_table_name(table_name, TableType.TEMP), table_name
    )

    # Assert table hasn't dropped
    table_names = persistent_data_store.get_table_names()
    assert get_table_name(table_name, TableType.TEMP) in table_names

    # Drop interim TEMP table
    persistent_data_store.drop_table(get_table_name(table_name, TableType.TEMP))

    # Assert temp table is dropped
    table_names = persistent_data_store.get_table_names()
    assert get_table_name(table_name, TableType.TEMP) not in table_names

    # Check if the new table is created
    assert table_name in table_names

    # Check if the new data is inserted
    result = persistent_data_store.duckdb_conn.execute(
        f"SELECT * FROM {table_name}"
    ).fetchall()

    assert len(result) == 3
    assert result[0][0] == "2022-01-01"
