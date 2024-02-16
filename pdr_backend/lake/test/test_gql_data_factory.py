from unittest.mock import patch
from io import StringIO
import sys
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory


def mock_fetch_function(network, st_ut, fin_ut, config):
    print(network, st_ut, fin_ut, config)
    return {}


def test_gql_data_factory():
    """
    Test GQLDataFactory initialization
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)
    assert len(gql_data_factory.record_config["tables"]) > 0
    assert gql_data_factory.record_config["config"] is not None
    assert gql_data_factory.ppss is not None


def test_update():
    """
    Test GQLDataFactory update calls the update function for all the tables
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    fns = {
        "pdr_predictions": mock_fetch_function,
        "pdr_subscriptions": mock_fetch_function,
        "pdr_truevals": mock_fetch_function,
        "pdr_payouts": mock_fetch_function,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    captured_output = StringIO()
    sys.stdout = captured_output
    gql_data_factory._update()

    printed_text = captured_output.getvalue().strip()
    count_updates = printed_text.count("Updating")
    assert count_updates == len(gql_data_factory.record_config["tables"].items())


@patch("pdr_backend.lake.gql_data_factory.Table.load")
def test_load_parquet(mock_load_table):
    """
    Test GQLDataFactory loads the data for all the tables
    """
    mock_load_table.return_value = []

    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    captured_output = StringIO()
    sys.stdout = captured_output
    gql_data_factory._load_parquet()

    printed_text = captured_output.getvalue().strip()
    count_loads = printed_text.count("Loading parquet for")
    assert count_loads == len(gql_data_factory.record_config["tables"].items())


@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._update")
@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._load_parquet")
def test_get_gql_tables(mock_load_parquet, mock_update):
    """
    Test GQLDataFactory's get_gql_tablesreturns all the tables
    """
    mock_load_parquet.return_value = None
    mock_update.return_value = None

    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    gql_dfs = gql_data_factory.get_gql_tables()

    assert len(gql_dfs.items()) == len(gql_data_factory.record_config["tables"].items())
