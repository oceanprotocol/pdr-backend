from unittest.mock import patch
from io import StringIO
import sys
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import TableType, get_table_name
from pdr_backend.lake.table_registry import TableRegistry
from pdr_backend.lake.test.resources import _clean_up_table_registry
from pdr_backend.lake.persistent_data_store import PersistentDataStore


def test_gql_data_factory():
    """
    Test GQLDataFactory initialization
    """
    _clean_up_table_registry()

    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    assert len(TableRegistry().get_tables()) > 0
    assert gql_data_factory.record_config["config"] is not None
    assert gql_data_factory.ppss is not None


def test_update_end_to_end(_mock_fetch_gql, tmpdir):
    """
    Test GQLDataFactory update calls the update function for all the tables
    """
    _clean_up_table_registry()

    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
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
        "pdr_slots": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    captured_output = StringIO()
    sys.stdout = captured_output
    gql_data_factory._update()

    printed_text = captured_output.getvalue().strip()
    count_updates = printed_text.count("Updating table")
    tables = TableRegistry().get_tables().items()
    assert count_updates == len(tables)


def test_update_partial_then_resume(
    _mock_fetch_gql, _get_test_PDS, _clean_up_test_folder, tmpdir
):
    """
    Test GQLDataFactory should update end-to-end, but fail in the middle
    Work 1: Update csv data (11-03 -> 11-05) and then fail inserting to db
    Work 2: Update and verify new records (11-05 -> 11-07) + table has all records (11-03 -> 11-07)
    """
    _clean_up_test_folder(tmpdir)
    _clean_up_table_registry()

    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Work 1: update csv files and insert into temp table
    fns = {
        "pdr_predictions": _mock_fetch_gql,
        "pdr_subscriptions": _mock_fetch_gql,
        "pdr_truevals": _mock_fetch_gql,
        "pdr_payouts": _mock_fetch_gql,
        "pdr_slots": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    with patch(
        "pdr_backend.lake.gql_data_factory.GQLDataFactory._move_from_temp_tables_to_live"
    ):
        for table_name in gql_data_factory.record_config["fetch_functions"]:
            gql_data_factory.record_config["fetch_functions"][table_name] = fns[
                table_name
            ]
        gql_data_factory._update()

        # Verify records exist in temp pred tables
        pds = _get_test_PDS(ppss.lake_ss.lake_dir)
        target_table_name = get_table_name("pdr_predictions", TableType.TEMP)
        target_records = pds.query_data("SELECT * FROM {}".format(target_table_name))

        assert len(target_records) == 2
        assert target_records["pair"].to_list() == ["ADA/USDT", "BNB/USDT"]
        assert target_records["timestamp"].to_list() == [1699038000000, 1699124400000]

    # Work 2: apply simulated error, update ppss "poorly", and verify it works as expected
    # Inject error by dropping db tables
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        pds.drop_table(get_table_name(table_name, TableType.TEMP))

    # manipulate ppss poorly and run gql_data_factory again
    gql_data_factory.ppss.lake_ss.d["st_timestr"] = "2023-11-01"
    gql_data_factory.ppss.lake_ss.d["fin_timestr"] = "2023-11-07"
    gql_data_factory._update()

    # Verify expected records were written to db
    target_table_name = get_table_name("pdr_predictions")
    target_records = pds.query_data("SELECT * FROM {}".format(target_table_name))
    assert len(target_records) == 4
    assert target_records["pair"].to_list() == [
        "ADA/USDT",
        "BNB/USDT",
        "ETH/USDT",
        "ETH/USDT",
    ]
    assert target_records["timestamp"].to_list() == [
        1699038000000,
        1699124400000,
        1699214400000,
        1699300800000,
    ]

def test_load_data(_mock_fetch_gql, _clean_up_test_folder, tmpdir):
    """
    Test GQLDataFactory update calls the getting the data from tables
    """
    _clean_up_test_folder(tmpdir)
    _clean_up_table_registry()

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
        "pdr_slots": _mock_fetch_gql,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for table_name in gql_data_factory.record_config["fetch_functions"]:
        gql_data_factory.record_config["fetch_functions"][table_name] = fns[table_name]

    gql_data_factory._update()

    temp_table_name = get_table_name("pdr_predictions", TableType.TEMP)

    all_reacords = PersistentDataStore(ppss.lake_ss.lake_dir).query_data(
        "SELECT * FROM {}".format(temp_table_name)
    )

    assert all_reacords is not None
    assert len(all_reacords) > 0
    assert all_reacords["pair"][0] == "BTC/USDT"
    assert all_reacords["timeframe"][0] == "5m"


@patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._update")
def test_get_gql_tables(mock_update):
    """
    Test GQLDataFactory's get_gql_tablesreturns all the tables
    """
    mock_update.return_value = None
    _clean_up_table_registry()

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

    assert len(gql_dfs.items()) == 5


def test_calc_start_ut(tmpdir):
    """
    Test GQLDataFactory's calc_start_ut returns the correct UnixTimeMs
    """
    _clean_up_table_registry()

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
    table = TableRegistry().get_table("pdr_predictions")

    st_ut = gql_data_factory._calc_start_ut(table)
    assert st_ut.to_seconds() == 1701561601


def test_do_subgraph_fetch(
    _mock_fetch_gql,
    _clean_up_test_folder,
    tmpdir,
):
    _clean_up_table_registry()

    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    _clean_up_test_folder(ppss.lake_ss.lake_dir)

    gql_data_factory = GQLDataFactory(ppss)

    table = TableRegistry().get_table("pdr_predictions")

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
