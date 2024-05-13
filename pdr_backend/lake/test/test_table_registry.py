from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.subgraph.slot import Slot
from pdr_backend.subgraph.subscription import Subscription


def _get_mock_ppss():
    return mock_ppss(
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        ".",
        st_timestr="2023-12-03",
        fin_timestr="2024-12-05",
    )


def test_table_registry():
    TableRegistry().register_table(Prediction, _get_mock_ppss())
    assert len(TableRegistry().get_tables()) == 1
    assert TableRegistry()._tables["pdr_predictions"].table_name == "pdr_predictions"


def test_register_tables():
    test_tables = [Prediction, Slot]

    TableRegistry().register_tables(test_tables, _get_mock_ppss())
    assert len(TableRegistry().get_tables()) == 2
    assert TableRegistry()._tables["pdr_predictions"].table_name == "pdr_predictions"
    assert TableRegistry()._tables["pdr_slots"].table_name == "pdr_slots"


def test_get_table():
    TableRegistry().register_table(Prediction, _get_mock_ppss())
    assert TableRegistry().get_table("pdr_predictions").table_name == "pdr_predictions"


def test_get_tables():
    test_tables = [Prediction, Subscription]
    TableRegistry().register_tables(test_tables, _get_mock_ppss())
    assert len(TableRegistry().get_tables()) == 2
    assert (
        TableRegistry().get_tables(["pdr_predictions"])["pdr_predictions"].table_name
        == "pdr_predictions"
    )
    assert (
        TableRegistry()
        .get_tables(["pdr_subscriptions"])["pdr_subscriptions"]
        .table_name
        == "pdr_subscriptions"
    )


def test_clear_tables():
    test_tables = [Prediction, Slot]

    TableRegistry().register_tables(test_tables, _get_mock_ppss())
    assert len(TableRegistry().get_tables()) == 2
    TableRegistry().clear_tables()
    assert len(TableRegistry().get_tables()) == 0
