import os

import polars as pl

from pdr_backend.lake.csv_data_store import (
    CSVDataStore,
    CSVDSIdentifier,
    _pad_with_zeroes,
)


def test_get_folder_path(_get_test_CSVDSIdentifier, tmpdir):
    csv_ds_identifier = _get_test_CSVDSIdentifier(tmpdir, "test")
    folder_path = csv_ds_identifier._get_folder_path()
    assert folder_path == f"{tmpdir}/test"


def test_create_file_name(_get_test_CSVDSIdentifier, tmpdir):
    csv_ds_identifier = _get_test_CSVDSIdentifier(tmpdir, "test")
    file_name = csv_ds_identifier._create_file_name(1707030362, 1709060200)
    print("file_name---", file_name)
    assert file_name == "test_from_1707030362_to_1709060200.csv"


def test_create_file_path(_get_test_CSVDSIdentifier, tmpdir):
    csv_ds_identifier = _get_test_CSVDSIdentifier(tmpdir, "test")
    file_path = csv_ds_identifier._create_file_path(1, 2)
    assert file_path == f"{tmpdir}/test/test_from_0000000001_to_0000000002.csv"


def test_create_file_path_without_endtime(_get_test_CSVDSIdentifier, tmpdir):
    csv_ds_identifier = _get_test_CSVDSIdentifier(tmpdir, "test")
    file_path = csv_ds_identifier._create_file_path(1, None)
    assert file_path == f"{tmpdir}/test/test_from_0000000001_to_.csv"


def test_read(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    identifier = CSVDSIdentifier(csv_data_store, "test")
    file_path = identifier._create_file_path(1, 2)

    with open(file_path, "w") as file:
        file.write("a,b,c\n1,2,3\n4,5,6")

    data = csv_data_store.read("test", 1, 2)
    assert data.equals(pl.DataFrame({"a": [1, 4], "b": [2, 5], "c": [3, 6]}))


def test_read_all(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    identifier = CSVDSIdentifier(csv_data_store, "test")

    file_path_1 = identifier._create_file_path(0, 20)
    file_path_2 = identifier._create_file_path(21, 41)

    with open(file_path_1, "w") as file:
        file.write("a,b,c\n1,2,3\n4,5,6")

    with open(file_path_2, "w") as file:
        file.write("a,b,c\n7,8,9\n10,11,12")

    data = csv_data_store.read_all("test")
    assert data["a"].to_list() == [1, 4, 7, 10]
    assert data["b"].to_list() == [2, 5, 8, 11]
    assert data["c"].to_list() == [3, 6, 9, 12]


def test_get_last_file_path(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    identifier = CSVDSIdentifier(csv_data_store, "test")

    file_path_1 = identifier._create_file_path(0, 20)
    file_path_2 = identifier._create_file_path(21, 41)
    file_path_3 = identifier._create_file_path(42, 62)
    file_path_4 = identifier._create_file_path(63, 83)

    files = [file_path_1, file_path_2, file_path_3, file_path_4]

    folder_path = identifier._get_folder_path()

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for file in files:
        # create empty files
        with open(os.path.join(folder_path, file), "w"):
            pass

    assert identifier._get_last_file_path() == os.path.join(folder_path, file_path_4)


def test_write(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    data = pl.DataFrame({"a": [1, 4], "b": [2, 5], "timestamp": [3, 6]})
    csv_data_store.write("test", data)

    identifier = CSVDSIdentifier(csv_data_store, "test")
    file_name = identifier._create_file_path(3, None)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == [1, 4]
    assert data["b"].to_list() == [2, 5]
    assert data["timestamp"].to_list() == [3, 6]


def test_write_1000_rows(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    data = pl.DataFrame(
        {
            "a": list(range(1000)),
            "b": list(range(1000)),
            "timestamp": list(range(1000)),
        }
    )
    csv_data_store.write("test", data)

    # folder_path = csv_data_store._get_folder_path("test")

    # get folder including files
    # folder = os.listdir(folder_path)
    # print folder files
    # print("folder---", folder)

    identifier = CSVDSIdentifier(csv_data_store, "test")
    file_name = identifier._create_file_path(0, 999)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == list(range(1000))
    assert data["b"].to_list() == list(range(1000))
    assert data["timestamp"].to_list() == list(range(1000))


def test_write_append(_get_test_CSVDS, tmpdir):
    csv_data_store = _get_test_CSVDS(tmpdir)
    data = pl.DataFrame({"a": [1, 4], "b": [2, 5], "timestamp": [3, 6]})
    csv_data_store.write("test", data)

    # new data
    data = pl.DataFrame({"a": [11, 41], "b": [21, 51], "timestamp": [31, 61]})
    csv_data_store.write("test", data)

    identifier = CSVDSIdentifier(csv_data_store, "test")
    file_name = identifier._create_file_path(3, 61)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == [1, 4, 11, 41]
    assert data["b"].to_list() == [2, 5, 21, 51]
    assert data["timestamp"].to_list() == [3, 6, 31, 61]


def test_pad_with_zeroes():
    assert _pad_with_zeroes(1, 10) == "0000000001"
    assert _pad_with_zeroes(100) == "0000000100"
    assert _pad_with_zeroes(1000) == "0000001000"


def test_get_to_value():
    csv_data_store = CSVDataStore("test")
    assert csv_data_store._get_to_value("test/test_from_0_to_0000000001.csv") == 1
    assert csv_data_store._get_to_value("test/test_from_0_to_0000000005.csv") == 5


def test_get_from_value():
    csv_data_store = CSVDataStore("test")
    assert (
        csv_data_store._get_from_value("test/test_from_0000000001_to_0000000001.csv")
        == 1
    )
    assert csv_data_store._get_from_value("test/test_from_0000000005_to_.csv") == 5


def test_multiton_instances():
    """
    This test is to check if the instances of
    the CSVDataStore are the same
    """
    CSVDataStore.clear_instances()
    csv_data_store_1 = CSVDataStore("test")
    csv_data_store_2 = CSVDataStore("test")
    assert csv_data_store_1 == csv_data_store_2
    assert csv_data_store_1 is csv_data_store_2
    assert csv_data_store_1.base_path == csv_data_store_2.base_path
    assert csv_data_store_1._instances == csv_data_store_2._instances


def test_multiton_instances_different_base_path():
    """
    This test is to check if the instances of
    the CSVDataStore are different
    """
    CSVDataStore.clear_instances()
    csv_data_store_1 = CSVDataStore("test")
    csv_data_store_2 = CSVDataStore("test2")
    assert csv_data_store_1 != csv_data_store_2
    assert csv_data_store_1 is not csv_data_store_2
    assert csv_data_store_1.base_path != csv_data_store_2.base_path
    assert csv_data_store_1._instances == csv_data_store_2._instances
