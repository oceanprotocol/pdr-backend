from unittest.mock import patch
from io import StringIO
import sys
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.util.time_types import UnixTimeMs


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


def test_update(_mock_fetch_gql, tmpdir):
    """
    Test GQLDataFactory update calls the update function for all the tables
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
    fns = {
        "pdr_predictions": _mock_fetch_gql,
        "pdr_subscriptions": _mock_fetch_gql,
        "pdr_truevals": _mock_fetch_gql,
        "pdr_payouts": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    captured_output = StringIO()
    sys.stdout = captured_output
    gql_data_factory._update()

    printed_text = captured_output.getvalue().strip()
    count_updates = printed_text.count("Updating table")
    tables = gql_data_factory.record_config["tables"].items()
    assert count_updates == len(tables)


def test_update_data(_mock_fetch_gql, _clean_up_test_folder, tmpdir):
    """
    Test GQLDataFactory update calls the update function for all the tables
    """
    _clean_up_test_folder(tmpdir)
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    fns = {
        "pdr_predictions": _mock_fetch_gql,
        "pdr_subscriptions": _mock_fetch_gql,
        "pdr_truevals": _mock_fetch_gql,
        "pdr_payouts": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    gql_data_factory._update()

    last_record = gql_data_factory.record_config["tables"][
        "pdr_predictions"
    ].get_pds_last_record()
    assert last_record is not None
    assert len(last_record) > 0
    assert last_record["pair"][0] == "BTC/USDT"
    assert last_record["timeframe"][0] == "5m"


def test_get_records(_mock_fetch_gql, _clean_up_test_folder, tmpdir):
    """
    Test GQLDataFactory get_records calls the update function for all the tables
    """
    _clean_up_test_folder(tmpdir)
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    fns = {
        "pdr_predictions": _mock_fetch_gql,
        "pdr_subscriptions": _mock_fetch_gql,
        "pdr_truevals": _mock_fetch_gql,
        "pdr_payouts": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    gql_data_factory._update()

    last_record = gql_data_factory.get_records("db")
    assert last_record is not None
    assert len(last_record) > 0
    assert last_record["pair"][0] == "BTC/USDT"
    assert last_record["timeframe"][0] == "5m"


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


def test_calc_start_ut(tmpdir):
    """
    Test GQLDataFactory's calc_start_ut returns the correct UnixTimeMs
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
    table = gql_data_factory.record_config["tables"]["pdr_predictions"]

    st_ut = gql_data_factory._calc_start_ut(table)
    assert st_ut.to_seconds() == 1701561601


def test_do_subgraph_fetch(
    _mock_fetch_gql,
    _clean_up_test_folder,
    tmpdir,
):
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up_test_folder(ppss.lake_ss.parquet_dir)

    gql_data_factory = GQLDataFactory(ppss)

    table = gql_data_factory.record_config["tables"]["pdr_predictions"]

    captured_output = StringIO()
    sys.stdout = captured_output
    gql_data_factory._do_subgraph_fetch(
        table,
        _mock_fetch_gql,
        "sapphire-mainnet",
        UnixTimeMs(1701634300000),
        UnixTimeMs(1701634500000),
        {"contract_list": ["0x123"]},
    )
    printed_text = captured_output.getvalue().strip()
    count_fetches = printed_text.count("Fetched")
    assert count_fetches == 1
