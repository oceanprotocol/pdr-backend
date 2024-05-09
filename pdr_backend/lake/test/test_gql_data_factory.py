from unittest.mock import patch
from unittest.mock import MagicMock
import polars as pl

from pdr_backend.lake.test.conftest import mock_daily_predictions
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.lake.persistent_data_store import PersistentDataStore
from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.table import TableType, get_table_name
from pdr_backend.lake.table_registry import TableRegistry


def test_gql_data_factory():
    """
    Test GQLDataFactory initialization
    """
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


def test_update_end_to_end(_mock_fetch_gql, tmpdir, caplog):
    """
    Test GQLDataFactory update calls the update function for all the tables
    """
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

    gql_data_factory._update()

    tables = TableRegistry().get_tables().items()
    assert caplog.text.count("Updating table") == len(tables)


def test_update_partial_then_resume(_mock_fetch_gql, _get_test_PDS, tmpdir):
    """
    Test GQLDataFactory should update end-to-end, but fail in the middle
    Work 1: Update csv data (11-03 -> 11-05) and then fail inserting to db
    Work 2: Update and verify new records (11-05 -> 11-07) + table has all records (11-03 -> 11-07)
    """
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
    pds = _get_test_PDS(ppss.lake_ss.lake_dir)
    pds.drop_table(get_table_name("pdr_predictions", TableType.TEMP))
    pds.drop_table(get_table_name("pdr_predictions", TableType.NORMAL))

    with patch(
        "pdr_backend.lake.gql_data_factory.GQLDataFactory._move_from_temp_tables_to_live"
    ):
        for table_name in gql_data_factory.record_config["fetch_functions"]:
            gql_data_factory.record_config["fetch_functions"][table_name] = fns[
                table_name
            ]
        gql_data_factory._update()

        # Verify records exist in temp pred tables
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
    gql_data_factory.ppss.lake_ss.d["st_timestr"] = "2023-11-05"
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

    assert len(gql_dfs.items()) == 5


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
    table = TableRegistry().get_table("pdr_predictions")

    st_ut = gql_data_factory._calc_start_ut(table)
    assert st_ut.to_seconds() == 1701561601


def test_calc_start_ut_from_predictions(_gql_datafactory_etl_predictions_df, tmpdir):
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

    st_ut = gql_data_factory._calc_start_ut_from_predictions()
    assert st_ut.to_seconds() == 1701561600

    ## Add some predictions
    table = TableRegistry().get_table("pdr_predictions")
    table.append_to_storage(_gql_datafactory_etl_predictions_df)

    st_ut = gql_data_factory._calc_start_ut_from_predictions()
    assert st_ut.to_seconds() == 1699300701


def test_do_subgraph_fetch(
    _mock_fetch_gql,
    tmpdir,
    caplog,
):
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    table = TableRegistry().get_table("pdr_predictions")

    gql_data_factory._do_subgraph_fetch(
        table,
        _mock_fetch_gql,
        "sapphire-mainnet",
        UnixTimeMs(1701634300000),
        UnixTimeMs(1701634500000),
        {"contract_list": ["0x123"]},
    )

    assert "Fetched" in caplog.text


def test_do_fetch_with_empty_data(
    _mock_fetch_empty_gql,
    tmpdir,
    caplog,
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

    gql_data_factory = GQLDataFactory(ppss)

    table = TableRegistry().get_table("pdr_predictions")

    gql_data_factory._do_subgraph_fetch(
        table,
        _mock_fetch_empty_gql,
        "sapphire-mainnet",
        UnixTimeMs(1701634300000),
        UnixTimeMs(1701634500000),
        {"contract_list": ["0x123"]},
    )

    assert "Fetched" in caplog.text

    # check if the db table is created

    temp_table_name = get_table_name("pdr_predictions", TableType.TEMP)
    pds = PersistentDataStore(ppss.lake_ss.lake_dir)
    all_tables = pds.get_table_names()

    assert temp_table_name in all_tables
    assert len(pds.query_data("SELECT * FROM {}".format(temp_table_name))) == 0


def test_do_subgraph_fetch_stop_loop_when_restarting_fetch(
    tmpdir,
    caplog,
):
    # If wrong timestamps in response data filter them out and stop the fetch loop

    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    table = TableRegistry().get_table("pdr_predictions")

    initial_response = mock_daily_predictions()
    mocked_function = MagicMock()

    assert len(initial_response) == 6

    # set wrong dates from the data within reponse
    initial_response[3].timestamp = 1697865200000
    initial_response[4].timestamp = 1697865700000
    initial_response[5].timestamp = 1697866200000

    mocked_function.return_value = initial_response

    gql_data_factory._do_subgraph_fetch(
        table,
        mocked_function,
        "sapphire-mainnet",
        UnixTimeMs(1698865200000),
        UnixTimeMs(1699300800000),
        {"contract_list": ["0x123"]},
    )
    temp_table_name = get_table_name("pdr_predictions", TableType.TEMP)
    pds = PersistentDataStore(ppss.lake_ss.lake_dir)
    all_tables = pds.get_table_names()

    assert temp_table_name in all_tables

    # check that data with wrong timestamp is filtered out
    assert len(pds.query_data("SELECT * FROM {}".format(temp_table_name))) == 3

    assert "Fetched" in caplog.text


def test_get_etl_st_fin(_gql_datafactory_etl_predictions_df, tmpdir):
    st_timestr = "2023-01-03"
    fin_timestr = "2024-05-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)
    gql_data_factory.record_config["gql_tables"] = ["pdr_predictions"]

    st_ut, fin_ut = gql_data_factory.get_etl_st_fin()

    assert st_ut is None
    assert fin_ut is None

    pds = PersistentDataStore(ppss.lake_ss.lake_dir)
    # Add some predictions
    pds.drop_table(get_table_name("pdr_predictions", TableType.TEMP))

    pds.insert_to_table(
        _gql_datafactory_etl_predictions_df,
        get_table_name("pdr_predictions", TableType.TEMP),
    )

    gql_data_factory._move_from_temp_tables_to_live()

    st_ut, fin_ut = gql_data_factory.get_etl_st_fin()

    assert st_ut.to_seconds() == 1672704000
    assert fin_ut.to_seconds() == 1699300700

def test_prepare_temp_table(
        _gql_datafactory_etl_predictions_df,
        _gql_datafactory_etl_predictions_df_second_part,
        tmpdir
    ):
    st_timestr = "2023-06-01"
    fin_timestr = "2024-05-05"
    ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)
    gql_data_factory.record_config["gql_tables"] = ["pdr_predictions"]

    pds = PersistentDataStore(ppss.lake_ss.lake_dir)
    csvds = CSVDataStore(ppss.lake_ss.lake_dir)
    # Add some predictions
    pds.drop_table(get_table_name("pdr_predictions", TableType.TEMP))
    csvds.delete("pdr_predictions")

    result = gql_data_factory._prepare_temp_table(
        table_name="pdr_predictions",
        st_ut=UnixTimeMs(ppss.lake_ss.st_timestamp), 
        fin_ut=UnixTimeMs(ppss.lake_ss.fin_timestamp),
        schema=_gql_datafactory_etl_predictions_df.schema
    )
    
    assert result is None

    csvds.write(
        dataset_identifier="pdr_predictions",
        data=_gql_datafactory_etl_predictions_df,
        schema=_gql_datafactory_etl_predictions_df.schema)

    result = gql_data_factory._prepare_temp_table(
        table_name="pdr_predictions",
        st_ut=UnixTimeMs(ppss.lake_ss.st_timestamp), 
        fin_ut=UnixTimeMs(ppss.lake_ss.fin_timestamp),
        schema=_gql_datafactory_etl_predictions_df.schema
    )

    assert result == _gql_datafactory_etl_predictions_df['timestamp'].max()

    queried_data = pds.query_data(
        "SELECT * FROM {}".format(get_table_name("pdr_predictions", TableType.TEMP)))

    print("queried_data--->", queried_data)
    assert queried_data['timestamp'].max() == _gql_datafactory_etl_predictions_df['timestamp'].max()

    csvds.write(
        dataset_identifier="pdr_predictions",
        data=_gql_datafactory_etl_predictions_df_second_part,
        schema=_gql_datafactory_etl_predictions_df.schema)

    result = gql_data_factory._prepare_temp_table(
        table_name="pdr_predictions",
        st_ut=UnixTimeMs(ppss.lake_ss.st_timestamp), 
        fin_ut=UnixTimeMs(ppss.lake_ss.fin_timestamp),
        schema=_gql_datafactory_etl_predictions_df_second_part.schema
    )

    assert result == _gql_datafactory_etl_predictions_df_second_part['timestamp'].max()

    pds.drop_table(get_table_name("pdr_predictions", TableType.TEMP))

    alternative_ppss = mock_ppss(
        ["binance BTC/USDT c 5m"],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr="2023-11-13",
    )

    alternative_gql_data_factory = GQLDataFactory(alternative_ppss)

    alternative_gql_data_factory.record_config["gql_tables"] = ["pdr_predictions"]

    result = gql_data_factory._prepare_temp_table(
        table_name="pdr_predictions",
        st_ut=UnixTimeMs(alternative_ppss.lake_ss.st_timestamp), 
        fin_ut=UnixTimeMs(alternative_ppss.lake_ss.fin_timestamp),
        schema=_gql_datafactory_etl_predictions_df_second_part.schema
    )

    assert result == 1699815500000
