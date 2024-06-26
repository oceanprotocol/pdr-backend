#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from typing import List

import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.csv_data_store import CSVDataStore
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.etl import ETL
from pdr_backend.lake.payout import Payout, mock_payout, mock_payouts
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.prediction import (
    Prediction,
    mock_daily_predictions,
    mock_first_predictions,
    mock_prediction,
    mock_second_predictions,
)
from pdr_backend.lake.slot import Slot, mock_slot, mock_slots
from pdr_backend.lake.subscription import mock_subscriptions
from pdr_backend.lake.table import NamedTable
from pdr_backend.lake.test.resources import (
    _gql_data_factory,
    get_filtered_timestamps_df,
)
from pdr_backend.lake.trueval import Trueval, mock_trueval, mock_truevals
from pdr_backend.util.time_types import UnixTimeMs


@pytest.fixture(autouse=True)
def clean_up_persistent_data_store(tmpdir):
    # Clean up duckDB
    db = DuckDBDataStore(str(tmpdir))

    # Select tables from duckdb
    table_names = db.get_table_names()

    # Drop the tables
    for table in table_names:
        db.execute_sql(f"DROP TABLE {table}")

    db.duckdb_conn.close()


@pytest.fixture()
def sample_payouts():
    return mock_payouts()


@pytest.fixture()
def sample_daily_predictions():
    return mock_daily_predictions()


@pytest.fixture()
def sample_subscriptions():
    return mock_subscriptions()


@pytest.fixture()
def sample_truevals():
    return mock_truevals()


@pytest.fixture()
def sample_slots():
    return mock_slots()


@pytest.fixture()
def _get_test_DuckDB():
    def create_duckdb_datastore(tmpdir):
        return DuckDBDataStore(str(tmpdir))

    return create_duckdb_datastore


@pytest.fixture()
def _get_test_CSVDataStore():
    def create_csv_datastore_identifier(tmpdir, name):
        return CSVDataStore(tmpdir, name)

    return create_csv_datastore_identifier


# pylint: disable=line-too-long
_ETL_PAYOUT_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1698865200-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1698865202,  # timestamp
        "ETH/USDT",  # token
        1698865200,  # slot # Nov 01 2023 19:00:00 GMT
        0.0,  # payout
        True,  # predictedValue
        # False,  # trueValue
        0.928046,  # revenue
        15.629683,  # roundSumStakesUp
        34.314841,  # roundSumStakes
        5.464642,  # stake
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152-1698951600-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1698951602,  # timestamp
        "BTC/USDT",  # token
        1698951600,  # slot # Nov 02 2023 19:00:00 GMT
        10.928642693189679,  # payout
        False,  # predictedValue
        # False,  # trueValue
        0.92804,  # revenue
        45.62968,  # roundSumStakesUp
        72.31484,  # roundSumStakes
        5.46464,  # stake
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1699038000-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1699038002,  # timestamp
        "ADA/USDT",  # token
        1699038000,  # slot # Nov 03 2023 19:00:00 GMT
        7.041434095860760067,  # payout
        False,  # predictedValue
        # False,  # trueValue
        0.93671,  # revenue
        47.61968,  # roundSumStakesUp
        72.31484,  # roundSumStakes
        3.4600000000000004,  # stake
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-1699124400-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1699124402,  # timestamp
        "BNB/USDT",
        1699124400,  # slot # Nov 04 2023 19:00:00 GMT
        7.160056238874628619,  # payout
        True,  # predictedValue
        # True,  # trueValue
        0.92804,  # revenue
        38.09065,  # roundSumStakesUp
        93.31532,  # roundSumStakes
        3.46000,  # stake
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699300800-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1699300802,  # timestamp
        "ETH/USDT",  # token
        1699300800,  # slot # Nov 06 2023 19:00:00 GMT
        0.0,  # payout
        True,  # predictedValue
        # False,  # trueValue
        0.92804,  # revenue
        47.71968,  # roundSumStakesUp
        74.30484,  # roundSumStakes
        3.4600000000000004,  # stake
    ),
]


# pylint: disable=line-too-long
_ETL_PREDICTIONS_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        None,
        None,
        None,
        1698865100,  # Nov 01 2023 19:00:00 GMT
        "binance",
        None,
        1698865200,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152",
        "BTC/USDT",
        "1h",
        None,
        None,
        None,
        1698951500,  # Nov 02 2023 19:00:00 GMT
        "binance",
        None,
        1698951600,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "ADA/USDT",
        "5m",
        None,
        None,
        None,
        1699037900,  # Nov 03 2023 19:00:00 GMT
        "binance",
        None,
        1699038000,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd",
        "BNB/USDT",
        "1h",
        None,
        None,
        None,
        1699124300,  # Nov 04 2023 19:00:00 GMT
        "kraken",
        None,
        1699124400,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "1h",
        None,
        None,
        None,
        1699214300,  # Nov 05 2023 19:00:00 GMT
        "binance",
        None,
        1699214400,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        None,
        None,
        None,
        1699300700,  # Nov 06 2023 19:00:00 GMT
        "binance",
        None,
        1699300800,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]


# pylint: disable=line-too-long
_ETL_TRUEVAL_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1698865200",
        1698865201,
        "ETH/USDT",
        True,
        1698865200,  # Nov 01 2023 19:00:00 GMT
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152-1698951600",
        1698951601,
        "BTC/USDT",
        True,
        1698951600,  # Nov 02 2023 19:00:00 GMT
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1699038000",
        1699038001,
        "ADA/USDT",
        False,
        1699038000,  # Nov 03 2023 19:00:00 GMT
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-1699124400",
        1699124401,
        "BNB/USDT",
        True,
        1699124400,  # Nov 04 2023 19:00:00 GMT
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699214300",
        1699214301,
        "ETH/USDT",
        False,
        1699214300,  # Nov 05 2023 19:00:00 GMT
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699300800",
        1699300801,
        "ETH/USDT",
        False,
        1699300800,  # Nov 06 2023 19:00:00 GMT
    ),
]


# pylint: disable=line-too-long
_ETL_SLOT_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1698865200",
        1698865200,
        1698865200,  # Nov 01 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152-1698951600",
        1698951600,
        1698951600,  # Nov 02 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1699038000",
        1699038000,
        1699038000,  # Nov 03 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-1699124400",
        1699124400,
        1699124400,  # Nov 04 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699214300",
        1699214300,
        1699214300,  # Nov 05 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699300800",
        1699300800,
        1699300800,  # Nov 06 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699315100",
        1699315100,
        1699315100,  # Nov 07 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699401600",
        1699401600,
        1699401600,  # Nov 08 2023 19:00:00 GMT
        None,
        None,
        None,
    ),
]


@enforce_types
def mock_etl_payouts() -> List[Payout]:
    return [mock_payout(payout_tuple) for payout_tuple in _ETL_PAYOUT_TUPS]


@enforce_types
def mock_etl_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple) for prediction_tuple in _ETL_PREDICTIONS_TUPS
    ]


@enforce_types
def mock_etl_truevals() -> List[Trueval]:
    return [mock_trueval(trueval_tuple) for trueval_tuple in _ETL_TRUEVAL_TUPS]


@enforce_types
def mock_etl_slots() -> List[Slot]:
    return [mock_slot(slot_tuple) for slot_tuple in _ETL_SLOT_TUPS]


@pytest.fixture()
def _gql_datafactory_etl_payouts_df():
    _payouts = mock_etl_payouts()
    payouts_df = _object_list_to_df(_payouts)
    payouts_df = payouts_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return payouts_df


@pytest.fixture()
def _gql_datafactory_etl_predictions_df():
    _predictions = mock_etl_predictions()
    predictions_df = _object_list_to_df(_predictions)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_etl_truevals_df():
    _truevals = mock_etl_truevals()
    truevals_df = _object_list_to_df(_truevals)
    truevals_df = truevals_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return truevals_df


@pytest.fixture()
def _gql_datafactory_etl_slots_df():
    _slots = mock_etl_slots()
    slots_df = _object_list_to_df(_slots)
    slots_df = slots_df.with_columns([pl.col("timestamp").mul(1000).alias("timestamp")])
    print("_gql_datafactory_etl_slots_df", slots_df)
    return slots_df


@pytest.fixture()
def _mock_fetch_gql():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_daily_predictions()

    return fetch_function


@pytest.fixture()
def _mock_fetch_gql_predictions():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_daily_predictions()

    return fetch_function


@pytest.fixture()
def _mock_fetch_gql_subscriptions():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_subscriptions()

    return fetch_function


@pytest.fixture()
def _mock_fetch_gql_truevals():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_truevals()

    return fetch_function


@pytest.fixture()
def _mock_fetch_gql_slots():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_slots()

    return fetch_function


@pytest.fixture()
def _mock_fetch_gql_payouts():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_payouts()

    return fetch_function


@pytest.fixture()
def _mock_fetch_empty_gql():
    # return a callable that returns a list of objects
    def fetch_function(
        network, st_ut, fin_ut, save_backoff_limit, pagination_limit, config
    ):
        print(
            f"{network}, {st_ut}, {fin_ut}, {save_backoff_limit}, {pagination_limit}, {config}"
        )
        return mock_first_predictions(0)

    return fetch_function


@pytest.fixture()
def _gql_datafactory_first_predictions_df():
    _predictions = mock_first_predictions()
    predictions_df = _object_list_to_df(_predictions)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_1k_predictions_df():
    _predictions = mock_first_predictions(500)
    predictions_df = _object_list_to_df(_predictions)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_second_predictions_df():
    _predictions = mock_second_predictions()
    predictions_df = _object_list_to_df(_predictions)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture(autouse=True)
def clean_up_test_folder():
    def _clean_up(tmpdir):
        for root, dirs, files in os.walk(tmpdir):
            for file in files:
                os.remove(os.path.join(root, file))
            for directory in dirs:
                # clean up the directory
                _clean_up(os.path.join(root, directory))
                os.rmdir(os.path.join(root, directory))

    return _clean_up


@pytest.fixture
def setup_data(
    _gql_datafactory_etl_payouts_df,
    _gql_datafactory_etl_predictions_df,
    _gql_datafactory_etl_truevals_df,
    _gql_datafactory_etl_slots_df,
    _get_test_DuckDB,
    tmpdir,
    request,
):
    st_timestr = request.param[0]
    fin_timestr = request.param[1]

    preds = get_filtered_timestamps_df(
        _gql_datafactory_etl_predictions_df, st_timestr, fin_timestr
    )
    truevals = get_filtered_timestamps_df(
        _gql_datafactory_etl_truevals_df, st_timestr, fin_timestr
    )
    payouts = get_filtered_timestamps_df(
        _gql_datafactory_etl_payouts_df, st_timestr, fin_timestr
    )
    slots = get_filtered_timestamps_df(
        _gql_datafactory_etl_slots_df, st_timestr, fin_timestr
    )

    ppss, gql_data_factory = _gql_data_factory(
        tmpdir,
        "binanceus ETH/USDT h 5m",
        st_timestr,
        fin_timestr,
    )

    gql_tables = {
        "pdr_predictions": NamedTable.from_dataclass(Prediction),
        "pdr_truevals": NamedTable.from_dataclass(Trueval),
        "pdr_payouts": NamedTable.from_dataclass(Payout),
        "pdr_slots": NamedTable.from_dataclass(Slot),
    }

    gql_tables["pdr_predictions"].append_to_storage(preds, ppss)
    gql_tables["pdr_truevals"].append_to_storage(truevals, ppss)
    gql_tables["pdr_payouts"].append_to_storage(payouts, ppss)
    gql_tables["pdr_slots"].append_to_storage(slots, ppss)

    assert ppss.lake_ss.st_timestamp == UnixTimeMs.from_timestr(st_timestr)
    assert ppss.lake_ss.fin_timestamp == UnixTimeMs.from_timestr(fin_timestr)

    # provide the setup data to the test
    etl = ETL(ppss, gql_data_factory)
    db = _get_test_DuckDB(tmpdir)

    assert etl is not None
    assert etl.gql_data_factory == gql_data_factory

    _records = db.query_data("SELECT * FROM pdr_predictions")
    assert len(_records) == 5

    yield etl, db, gql_tables
