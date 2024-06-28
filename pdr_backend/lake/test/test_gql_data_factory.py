#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from unittest.mock import MagicMock, patch

import polars as pl

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
from pdr_backend.lake.table import Table, TempTable, NewEventsTable, UpdateEventsTable
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
    _gql_datafactory_etl_predictions_df,
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

    work_1_expected_predictions = _gql_datafactory_etl_predictions_df.filter(
        pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr)
    ).filter(pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    assert len(work_1_expected_predictions) == 2, "Expected 2 records"

    gql_data_factory = GQLDataFactory(ppss)
    with patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._do_swap_to_prod"):
        for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
            dataclass.get_fetch_function = MagicMock(return_value=fns[dataclass])

        gql_data_factory._update()

        # Verify records exist in new_events table
        db = _get_test_DuckDB(ppss.lake_ss.lake_dir)
        target_table = NewEventsTable.from_dataclass(Prediction)
        target_records = db.query_data(
            "SELECT * FROM {}".format(target_table.table_name)
        )

        assert len(target_records) == 2
        assert len(target_records) == len(work_1_expected_predictions)
        assert target_records["pair"].to_list() == ["ADA/USDT", "BNB/USDT"]
        assert target_records["timestamp"].to_list() == [1699038000000, 1699124400000]

    # Work 2: apply simulated error, update ppss "poorly", and verify it works as expected
    # Inject error by dropping db tables
    for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
        db.drop_table(NewEventsTable.from_dataclass(dataclass).table_name)
        db.drop_table(TempTable.from_dataclass(dataclass).table_name)
        db.drop_table(Table.from_dataclass(dataclass).table_name)

    target_table = NewEventsTable.from_dataclass(dataclass)
    target_records = db.query_data("SELECT * FROM {}".format(target_table.table_name))
    assert target_records is None

    target_table = TempTable.from_dataclass(dataclass)
    target_records = db.query_data("SELECT * FROM {}".format(target_table.table_name))
    assert target_records is None

    target_table = Table.from_dataclass(dataclass)
    target_records = db.query_data("SELECT * FROM {}".format(target_table.table_name))
    assert target_records is None

    # Validate expected records we'll be finding
    st_timestr = "2023-11-03"
    fin_timestr = "2023-11-07"

    work_2_expected_predictions = [
        x
        for x in mock_daily_predictions()
        if UnixTimeMs.from_timestr(st_timestr)
        <= x.timestamp * 1000
        <= UnixTimeMs.from_timestr(fin_timestr)
    ]
    assert len(work_2_expected_predictions) == 4, "Expected 4 records"

    # manipulate ppss poorly and run gql_data_factory again
    gql_data_factory.ppss.lake_ss.d["st_timestr"] = st_timestr
    gql_data_factory.ppss.lake_ss.d["fin_timestr"] = fin_timestr

    # patch GQL to pre-process predictions that should already exist in CSV
    with patch(
        "pdr_backend.lake.gql_data_factory.GQLDataFactory._prepare_subgraph_fetch",
        return_value=None,
    ):
        new_events_table = NewEventsTable.from_dataclass(Prediction)
        new_events_table._append_to_db(work_1_expected_predictions, ppss)
        gql_data_factory._update()

    # Verify expected records were written to db
    target_table = Table.from_dataclass(Prediction)
    target_records = db.query_data("SELECT * FROM {}".format(target_table.table_name))
    assert len(target_records) == 4, "Expected 4 records"
    assert len(target_records) == len(
        work_2_expected_predictions
    ), "Expected records to match"

    assert target_records["pair"].to_list() == [
        "ADA/USDT",
        "BNB/USDT",
        "ETH/USDT",
        "ETH/USDT",
    ]

    assert target_records["timestamp"].to_list() == [
        1699037900000,
        1699124300000,
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
    table = Table.from_dataclass(Prediction)

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

    new_events_table = NewEventsTable("pdr_predictions")
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    all_tables = db.get_table_names()

    assert new_events_table.table_name in all_tables
    assert (
        len(db.query_data("SELECT * FROM {}".format(new_events_table.table_name))) == 0
    )


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
    new_events_table = NewEventsTable("pdr_predictions")
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)
    all_tables = db.get_table_names()

    assert new_events_table.table_name in all_tables
    assert (
        len(db.query_data("SELECT * FROM {}".format(new_events_table.table_name))) == 3
    )
    assert "Fetched" in caplog.text


def test_prepare_subgraph_fetch_empty_prod(
    _gql_datafactory_etl_predictions_df,
    _mock_fetch_gql_predictions,
    _mock_fetch_gql_subscriptions,
    _mock_fetch_gql_truevals,
    _mock_fetch_gql_payouts,
    _mock_fetch_gql_slots,
    _get_test_DuckDB,
    tmpdir,
):
    """
    Test that validates:
    1. after production table is created
    2. we drop values from the production table
    3. prepare_subgraph_fetch() is called to pre-load data from CSV
    4. pipeline resumes from latest CSV records
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
    db = DuckDBDataStore(ppss.lake_ss.lake_dir)

    fns = {
        Prediction: _mock_fetch_gql_predictions,
        Subscription: _mock_fetch_gql_subscriptions,
        Trueval: _mock_fetch_gql_truevals,
        Payout: _mock_fetch_gql_payouts,
        Slot: _mock_fetch_gql_slots,
    }
    gql_data_factory = GQLDataFactory(ppss)

    # Work 1: We're going to validate that the expected data is processed
    # From: Subgraph
    # To: CSV + DB Prod tables
    # patch GQL to only process predictions (all daa)
    work_1_expected_predictions = _gql_datafactory_etl_predictions_df.filter(
        pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr)
    ).filter(pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    assert len(work_1_expected_predictions) == 2, "Expected 2 records"

    work_1_data = None
    with patch("pdr_backend.lake.gql_data_factory.GQLDataFactory._do_swap_to_prod"):
        for dataclass in _GQLDF_REGISTERED_LAKE_TABLES:
            dataclass.get_fetch_function = MagicMock(return_value=fns[dataclass])
        gql_data_factory._update()

        db = _get_test_DuckDB(ppss.lake_ss.lake_dir)
        target_table = NewEventsTable.from_dataclass(Prediction)
        work_1_data = db.query_data("SELECT * FROM {}".format(target_table.table_name))

        assert len(work_1_data) == 2
        assert len(work_1_data) == len(work_1_expected_predictions)

        assert work_1_data["pair"].to_list() == ["ADA/USDT", "BNB/USDT"]
        assert work_1_data["timestamp"].to_list() == [1699038000000, 1699124400000]

    # Work 2: We're going to drop records from prod
    # We're going to assert that the data will be correctly loaded from CSV
    # We'll then verify that everything resumes and is processed correctly
    # Drop any tables
    db.drop_table(Table.from_dataclass(Prediction).table_name)
    db.drop_table(NewEventsTable.from_dataclass(Prediction).table_name)
    db.drop_table(UpdateEventsTable.from_dataclass(Prediction).table_name)

    # verify that subgraph prepares everything correctly
    gql_data_factory._prepare_subgraph_fetch(
        Prediction,
        UnixTimeMs.from_timestr(st_timestr),
        UnixTimeMs.from_timestr(fin_timestr),
    )

    # assert that the data was loaded from CSV to the temp table
    work_2_data = db.query_data(
        "SELECT * FROM {}".format(NewEventsTable.from_dataclass(Prediction).table_name)
    )
    assert len(work_2_data) == 2
    assert len(work_2_data) == len(work_1_data)

    # Work 3: We're going to drop Work 2 records and run it again e2e
    # This time, we'll adjust the end date so we should have data from csvs + subgraph
    # From the CSV + the rest from the mock_daily_predictions
    # Drop any tables
    db.drop_table(Table.from_dataclass(Prediction).table_name)
    db.drop_table(NewEventsTable.from_dataclass(Prediction).table_name)
    db.drop_table(UpdateEventsTable.from_dataclass(Prediction).table_name)

    fin_timestr = "2023-11-07"
    work_3_expected_data = _gql_datafactory_etl_predictions_df.filter(
        pl.col("timestamp") >= UnixTimeMs.from_timestr(st_timestr)
    ).filter(pl.col("timestamp") <= UnixTimeMs.from_timestr(fin_timestr))
    assert len(work_3_expected_data) == 4, "Expected 4 records"

    # verify that subgraph prepares everything correctly
    gql_data_factory.ppss.lake_ss.d["fin_timestr"] = fin_timestr

    # patch GQL to only process predictions (all daa)
    with patch(
        "pdr_backend.lake.gql_data_factory.GQLDataFactory._prepare_subgraph_fetch",
        return_value=None,
    ):
        with patch(
            "pdr_backend.lake.gql_data_factory._GQLDF_REGISTERED_LAKE_TABLES",
            [Prediction],
        ):
            new_events_table = NewEventsTable.from_dataclass(Prediction)
            new_events_table._append_to_db(work_1_data, ppss)
            gql_data_factory._update()

    # assert that the data was loaded from CSV to the temp table
    work_3_data = db.query_data(
        "SELECT * FROM {}".format(Table.from_dataclass(Prediction).table_name)
    )
    assert len(work_3_data) == 4
    assert len(work_3_data) == len(work_3_expected_data)
