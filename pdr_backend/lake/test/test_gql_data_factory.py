from unittest.mock import MagicMock, patch

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.gql_data_factory import (
    _GQLDF_REGISTERED_LAKE_TABLES,
    _GQLDF_REGISTERED_TABLE_NAMES,
    GQLDataFactory,
)
from pdr_backend.lake.payout import Payout
from pdr_backend.lake.prediction import Prediction, mock_daily_predictions
from pdr_backend.lake.slot import Slot
from pdr_backend.lake.subscription import Subscription
from pdr_backend.lake.table import NamedTable, TempTable
from pdr_backend.lake.trueval import Trueval
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.util.time_types import UnixTimeMs


def test_gql_data_factory():
    """
    Test GQLDataFactory initialization
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2023-12-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        ".",
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    assert gql_data_factory.record_config["config"] is not None
    assert gql_data_factory.ppss is not None


def test_update_end_to_end(
    _mock_fetch_gql_predictions,
    _mock_fetch_gql_subscriptions,
    _mock_fetch_gql_truevals,
    _mock_fetch_gql_payouts,
    _mock_fetch_gql_slots,
    tmpdir,
    caplog,
):
    """
    Test GQLDataFactory update calls the update function for all the tables
    """
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )
    fns = {
        Prediction: _mock_fetch_gql_predictions,
        Subscription: _mock_fetch_gql_subscriptions,
        Trueval: _mock_fetch_gql_truevals,
        Payout: _mock_fetch_gql_payouts,
        Slot: _mock_fetch_gql_slots,
    }

    gql_data_factory = GQLDataFactory(ppss)
    for dataclass in fns:
        dataclass.get_fetch_function = MagicMock(return_value=fns[dataclass])

    gql_data_factory._update()

    assert caplog.text.count("Updating table") == len(_GQLDF_REGISTERED_TABLE_NAMES)


def test_update_partial_then_resume(
    _mock_fetch_gql_predictions,
    _mock_fetch_gql_subscriptions,
    _mock_fetch_gql_truevals,
    _mock_fetch_gql_payouts,
    _mock_fetch_gql_slots,
    _get_test_DuckDB,
    tmpdir,
):
    """
    Test GQLDataFactory should update end-to-end, but fail in the middle
    Work 1: Update csv data (11-03 -> 11-05) and then fail inserting to db
    Work 2: Update and verify new records (11-05 -> 11-07) + table has all records (11-03 -> 11-07)
    """
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    # Work 1: update csv files and insert into temp table
    fns = {
        Prediction: _mock_fetch_gql_predictions,
        Subscription: _mock_fetch_gql_subscriptions,
        Trueval: _mock_fetch_gql_truevals,
        Payout: _mock_fetch_gql_payouts,
        Slot: _mock_fetch_gql_slots,
    }

    gql_data_factory = GQLDataFactory(ppss)
    with patch(
        "pdr_backend.lake.gql_data_factory.GQLDataFactory._move_from_temp_tables_to_live"
    ):
        for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
            dataclass.get_fetch_function = MagicMock(return_value=fns[dataclass])

        gql_data_factory._update()

        # Verify records exist in temp pred tables
        db = _get_test_DuckDB(ppss.lake_ss.lake_dir)
        target_table_name = TempTable("pdr_predictions").fullname
        target_records = db.query_data("SELECT * FROM {}".format(target_table_name))

        assert len(target_records) == 2
        assert target_records["pair"].to_list() == ["ADA/USDT", "BNB/USDT"]
        assert target_records["timestamp"].to_list() == [1699038000000, 1699124400000]

    # Work 2: apply simulated error, update ppss "poorly", and verify it works as expected
    # Inject error by dropping db tables
    for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
        db.drop_table(TempTable.from_dataclass(dataclass).fullname)

    # manipulate ppss poorly and run gql_data_factory again
    gql_data_factory.ppss.lake_ss.d["st_timestr"] = "2023-11-01"
    gql_data_factory.ppss.lake_ss.d["fin_timestr"] = "2023-11-07"
    gql_data_factory._update()

    # Verify expected records were written to db
    target_table_name = NamedTable("pdr_predictions").fullname
    target_records = db.query_data("SELECT * FROM {}".format(target_table_name))
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


def test_calc_start_ut(tmpdir):
    """
    Test GQLDataFactory's calc_start_ut returns the correct UnixTimeMs
    """
    st_timestr = "2023-12-03"
    fin_timestr = "2024-12-05"
    ppss = mock_ppss(
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)
    table = NamedTable.from_dataclass(Prediction)

    st_ut = gql_data_factory._calc_start_ut(table)
    assert st_ut.to_seconds() == 1701561601


def test_do_subgraph_fetch(
    _mock_fetch_gql,
    tmpdir,
    caplog,
):
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    gql_data_factory._do_subgraph_fetch(
        Prediction,
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
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    gql_data_factory._do_subgraph_fetch(
        Prediction,
        "sapphire-mainnet",
        UnixTimeMs(1701634300000),
        UnixTimeMs(1701634500000),
        {"contract_list": ["0x123"]},
    )

    assert "Fetched" in caplog.text

    # check if the db table is created

    temp_table_name = TempTable("pdr_predictions").fullname
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    all_tables = db.get_table_names()

    assert temp_table_name in all_tables
    assert len(db.query_data("SELECT * FROM {}".format(temp_table_name))) == 0


def test_do_subgraph_fetch_stop_loop_when_restarting_fetch(
    tmpdir,
    caplog,
):
    # If wrong timestamps in response data filter them out and stop the fetch loop

    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    initial_response = mock_daily_predictions()

    assert len(initial_response) == 6

    # set wrong dates from the data within reponse
    initial_response[3].timestamp = 1697865200000
    initial_response[4].timestamp = 1697865700000
    initial_response[5].timestamp = 1697866200000

    mocked_function = MagicMock()
    mocked_function.return_value = initial_response
    Prediction.get_fetch_function = MagicMock(return_value=mocked_function)

    gql_data_factory._do_subgraph_fetch(
        Prediction,
        "sapphire-mainnet",
        UnixTimeMs(1698865200000),
        UnixTimeMs(1699300800000),
        {"contract_list": ["0x123"]},
    )
    temp_table_name = TempTable("pdr_predictions").fullname
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    all_tables = db.get_table_names()

    assert temp_table_name in all_tables

    # check that data with wrong timestamp is filtered out
    assert len(db.query_data("SELECT * FROM {}".format(temp_table_name))) == 3

    assert "Fetched" in caplog.text


def test_prepare_temp_table_get_data_from_csv_if_production_table_empty(tmpdir):
    """
    Test that after production table is created and then values are deleted,
    prepare_temp_table gets data from csv and adds to temp table without errors.
    """
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-05"
    ppss = mock_ppss(
        [{"train_on": "binance BTC/USDT c 5m", "predict": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr=st_timestr,
        fin_timestr=fin_timestr,
    )

    gql_data_factory = GQLDataFactory(ppss)

    table = NamedTable.from_dataclass(Prediction)
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)

    initial_response = mock_daily_predictions()
    assert len(initial_response) == 6

    mocked_function = MagicMock()
    mocked_function.return_value = initial_response
    Prediction.get_fetch_function = MagicMock(return_value=mocked_function)

    # temp table and csv should be created with the initial data
    gql_data_factory._do_subgraph_fetch(
        Prediction,
        "sapphire-mainnet",
        UnixTimeMs(1698865200000),
        UnixTimeMs(1699300800000),
        {"contract_list": ["0x123"]},
    )
    assert (
        len(db.query_data("SELECT * FROM {}".format("_temp_{}".format(table.fullname))))
        == 6
    )

    # move temp table to production and check the data is there
    db.move_table_data(TempTable.from_dataclass(Prediction), table)

    # now keep both temp and production tables but remove values
    db.query_data("DELETE FROM {}".format(table.fullname))
    db.query_data("DELETE FROM {}".format("_temp_{}".format(table.fullname)))
    assert len(db.query_data("SELECT * FROM {}".format(table.fullname))) == 0

    # run prepare_temp_table again to check that,
    # if production table doesn't have any rows doesn't break the preparation
    gql_data_factory._prepare_temp_table(
        Prediction,
        UnixTimeMs(1699300800000),
        UnixTimeMs(1699300800000),
    )
    db.move_table_data(TempTable.from_dataclass(Prediction), table)

    assert len(db.query_data("SELECT * FROM {}".format(table.fullname))) == 6
