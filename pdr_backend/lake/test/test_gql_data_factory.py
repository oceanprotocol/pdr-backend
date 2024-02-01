from unittest.mock import patch
from io import StringIO
import sys
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory


def test_gql_data_factory():
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


@patch("pdr_backend.lake.gql_data_factory.Table.update")
def test_update(mock_update_table):
    mock_update_table.return_value = {}

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
    gql_data_factory._update()

    printed_text = captured_output.getvalue().strip()
    count_updates = printed_text.count("Updating")
    assert count_updates == len(gql_data_factory.record_config["tables"].items())


@patch("pdr_backend.lake.gql_data_factory.Table.load")
def test_load_parquet(mock_load_table):
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
def test_get_gql_dfs(mock_load_parquet, mock_update):
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

    gql_dfs = gql_data_factory.get_gql_dfs()

    assert len(gql_dfs.items()) == len(gql_data_factory.record_config["tables"].items())
