import os

import polars as pl
from pdr_backend.lake.csv_data_store import CSVDataStore


def _get_test_manager(tmpdir):
    return CSVDataStore(str(tmpdir))


def _clean_up(tmpdir):
    for root, dirs, files in os.walk(tmpdir):
        for file in files:
            os.remove(os.path.join(root, file))
        for directory in dirs:
            # clean up the directory
            _clean_up(os.path.join(root, directory))
            os.rmdir(os.path.join(root, directory))


def test_get_folder_path(tmpdir):
    manager = _get_test_manager(tmpdir)
    folder_path = manager._get_folder_path("test")
    assert folder_path == f"{tmpdir}/test"


def test_create_file_name(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_name = manager._create_file_name("test", 1707030362, 1709060200)
    print("file_name---", file_name)
    assert file_name == "test_from_1707030362_to_1709060200.csv"


def test_get_file_paths(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_name_1 = manager._create_file_name("test", 0, 20)
    file_name_2 = manager._create_file_name("test", 21, 40)
    file_name_3 = manager._create_file_name("test", 41, 60)
    file_name_4 = manager._create_file_name("test", 61, 80)

    files = [file_name_1, file_name_2, file_name_3, file_name_4]

    folder_path = manager._get_folder_path("test")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for file in files:
        # create empty files
        with open(os.path.join(folder_path, file), "w"):
            pass

    # check if empty files are created
    for file in files:
        assert os.path.exists(folder_path + "/" + file)

    file_paths = manager._get_file_paths(folder_path, 21, 60)

    for file_path in file_paths:
        assert file_path in [
            folder_path + "/" + file_name_2,
            folder_path + "/" + file_name_3,
        ]

    _clean_up(tmpdir)


def test_create_file_path(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_path = manager._create_file_path("test", 1, 2)
    assert file_path == f"{tmpdir}/test/test_from_0000000001_to_0000000002.csv"


def test_create_file_path_without_endtime(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_path = manager._create_file_path("test", 1, None)
    assert file_path == f"{tmpdir}/test/test_from_0000000001_to_.csv"


def test_read(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_path = manager._create_file_path("test", 1, 2)

    with open(file_path, "w") as file:
        file.write("a,b,c\n1,2,3\n4,5,6")

    data = manager.read("test", 1, 2)
    assert data.equals(pl.DataFrame({"a": [1, 4], "b": [2, 5], "c": [3, 6]}))

    _clean_up(tmpdir)


def test_read_all(tmpdir):
    manager = _get_test_manager(tmpdir)

    file_path_1 = manager._create_file_path("test", 0, 20)
    file_path_2 = manager._create_file_path("test", 21, 41)

    with open(file_path_1, "w") as file:
        file.write("a,b,c\n1,2,3\n4,5,6")

    with open(file_path_2, "w") as file:
        file.write("a,b,c\n7,8,9\n10,11,12")

    data = manager.read_all("test")
    assert data["a"].to_list() == [1, 4, 7, 10]
    assert data["b"].to_list() == [2, 5, 8, 11]
    assert data["c"].to_list() == [3, 6, 9, 12]

    _clean_up(tmpdir)


def test_get_last_file_path(tmpdir):
    manager = _get_test_manager(tmpdir)
    file_path_1 = manager._create_file_path("test", 0, 20)
    file_path_2 = manager._create_file_path("test", 21, 41)
    file_path_3 = manager._create_file_path("test", 42, 62)
    file_path_4 = manager._create_file_path("test", 63, 83)

    files = [file_path_1, file_path_2, file_path_3, file_path_4]

    folder_path = manager._get_folder_path("test")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    for file in files:
        # create empty files
        with open(os.path.join(folder_path, file), "w"):
            pass

    assert manager._get_last_file_path(f"{tmpdir}/test") == os.path.join(
        folder_path, file_path_4
    )

    _clean_up(tmpdir)


def test_write(tmpdir):
    manager = _get_test_manager(tmpdir)
    data = pl.DataFrame({"a": [1, 4], "b": [2, 5], "timestamp": [3, 6]})
    manager.write("test", data)
    file_name = manager._create_file_path("test", 3, None)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == [1, 4]
    assert data["b"].to_list() == [2, 5]
    assert data["timestamp"].to_list() == [3, 6]

    _clean_up(tmpdir)


def test_write_1000_rows(tmpdir):
    _clean_up(tmpdir)

    manager = _get_test_manager(tmpdir)
    data = pl.DataFrame(
        {
            "a": list(range(1000)),
            "b": list(range(1000)),
            "timestamp": list(range(1000)),
        }
    )
    manager.write("test", data)

    #folder_path = manager._get_folder_path("test")

    # get folder including files
    # folder = os.listdir(folder_path)
    # print folder files
    # print("folder---", folder)

    file_name = manager._create_file_path("test", 0, 999)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == list(range(1000))
    assert data["b"].to_list() == list(range(1000))
    assert data["timestamp"].to_list() == list(range(1000))

    _clean_up(tmpdir)


def test_write_append(tmpdir):
    manager = _get_test_manager(tmpdir)
    data = pl.DataFrame({"a": [1, 4], "b": [2, 5], "timestamp": [3, 6]})
    manager.write("test", data)

    # new data
    data = pl.DataFrame({"a": [11, 41], "b": [21, 51], "timestamp": [31, 61]})
    manager.write("test", data)

    file_name = manager._create_file_path("test", 3, 61)

    data = pl.read_csv(file_name)

    assert data["a"].to_list() == [1, 4, 11, 41]
    assert data["b"].to_list() == [2, 5, 21, 51]
    assert data["timestamp"].to_list() == [3, 6, 31, 61]

    _clean_up(tmpdir)


def test_fill_with_zero():
    manager = CSVDataStore("test")
    assert manager._fill_with_zero(1, 10) == "0000000001"
    assert manager._fill_with_zero(100) == "0000000100"
    assert manager._fill_with_zero(1000) == "0000001000"


def test_get_to_value():
    manager = CSVDataStore("test")
    assert manager._get_to_value("test/test_from_0_to_0000000001.csv") == 1
    assert manager._get_to_value("test/test_from_0_to_0000000005.csv") == 5


def test_get_from_value():
    manager = CSVDataStore("test")
    assert manager._get_from_value("test/test_from_0000000001_to_0000000001.csv") == 1
    assert manager._get_from_value("test/test_from_0000000005_to_.csv") == 5
