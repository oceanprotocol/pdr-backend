from unittest.mock import patch
from io import StringIO
import sys
import polars as pl
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory


def mock_fetch_function(
    network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
):
    print(network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config)
    return []


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


def test_load_parquet(tmpdir):
    """
    Test GQLDataFactory loads the data for all the tables
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    assert len(gql_data_factory.record_config["tables"].items()) == 4

    table = gql_data_factory.record_config["tables"]["pdr_predictions"]

    assert table is not None
    assert type(table.df) == pl.DataFrame
    assert table.df.schema == table.df_schema


@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._update")
def test_get_gql_tables(mock_update):
    """
    Test GQLDataFactory's get_gql_tablesreturns all the tables
    """
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
