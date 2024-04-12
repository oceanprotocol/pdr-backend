from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.ppss.ppss import mock_ppss


def _get_mock_ppss():
    return mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr="2023-12-03",
        fin_timestr="2024-12-05",
    )


def test_table_registry():
    TableRegistry().register_table(
        "test_table", ("test_table", {"test": "test"}, _get_mock_ppss())
    )
    assert len(TableRegistry().get_tables()) == 1
    assert TableRegistry()._tables["test_table"].table_name == "test_table"


def test_register_tables():
    test_tables = {
        "test_table": ("test_table", {"test": "test"}, _get_mock_ppss()),
        "test_table2": ("test_table2", {"test": "test"}, _get_mock_ppss()),
    }

    TableRegistry().register_tables(test_tables)
    assert len(TableRegistry().get_tables()) == 2
    assert TableRegistry()._tables["test_table"].table_name == "test_table"
    assert TableRegistry()._tables["test_table2"].table_name == "test_table2"


def test_get_table():
    TableRegistry().register_table(
        "test_table", ("test_table", {"test": "test"}, _get_mock_ppss())
    )
    assert TableRegistry().get_table("test_table").table_name == "test_table"


def test_get_tables():
    test_tables = {
        "test_table": ("test_table", {"test": "test"}, _get_mock_ppss()),
        "test_table2": ("test_table2", {"test": "test"}, _get_mock_ppss()),
    }

    TableRegistry().register_tables(test_tables)
    assert len(TableRegistry().get_tables()) == 2
    assert (
        TableRegistry().get_tables(["test_table"])["test_table"].table_name
        == "test_table"
    )
    assert (
        TableRegistry().get_tables(["test_table2"])["test_table2"].table_name
        == "test_table2"
    )


def test_clear_tables():
    test_tables = {
        "test_table": ("test_table", {"test": "test"}, _get_mock_ppss()),
        "test_table2": ("test_table2", {"test": "test"}, _get_mock_ppss()),
    }

    TableRegistry().register_tables(test_tables)
    assert len(TableRegistry().get_tables()) == 2
    TableRegistry().clear_tables()
    assert len(TableRegistry().get_tables()) == 0
