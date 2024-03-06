from pdr_backend.lake.base_data_store import BaseDataStore
import duckdb


def _get_data_store(tmpdir):
    return BaseDataStore(str(tmpdir))


def test__duckdb_connection(tmpdir):
    """
    Test datastore.
    """
    data_store = _get_data_store(tmpdir)
    assert isinstance(
        data_store.duckdb_conn, duckdb.DuckDBPyConnection
    ), "The connection is not a DuckDBPyConnection"
