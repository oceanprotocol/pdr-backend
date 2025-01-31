import pytest

from pdr_backend.lake.csv_data_store import CSVDataStore


@pytest.fixture()
def _get_test_CSVDataStore():
    def create_csv_datastore_identifier(tmpdir, name):
        return CSVDataStore(tmpdir, name)

    return create_csv_datastore_identifier
