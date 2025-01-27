from pdr_backend.lake.base_data_store import BaseDataStore


def test_base_data_store_init():
    base_data_store = BaseDataStore("test")
    assert base_data_store.base_path == "test"
    assert base_data_store._instances == {"test_0": base_data_store}
    base_data_store._instances = {}


def test_clear_base_data_store():
    BaseDataStore._instances = {}
    assert BaseDataStore._instances == {}

    base_data_store = BaseDataStore("test")
    assert BaseDataStore._instances == {"test_0": base_data_store}
    BaseDataStore.clear_instances()
    assert BaseDataStore._instances == {}
