from typing import List
from enforce_typing import enforce_types
import pytest
import polars as pl

from pdr_backend.subgraph.prediction import (
    Prediction,
    mock_daily_predictions,
    mock_prediction,
)
from pdr_backend.subgraph.subscription import mock_subscriptions
from pdr_backend.subgraph.trueval import Trueval, mock_truevals, mock_trueval
from pdr_backend.subgraph.payout import Payout, mock_payouts, mock_payout
from pdr_backend.subgraph.slot import Slot, mock_slots, mock_slot

from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.lake.table_pdr_slots import slots_schema
from pdr_backend.lake.table_pdr_payouts import payouts_schema
from pdr_backend.lake.table_pdr_predictions import predictions_schema
from pdr_backend.lake.table_pdr_truevals import truevals_schema


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
        0.0,  # revenue
        0.0,  # roundSumStakesUp
        0.0,  # roundSumStakes
        5.464642693189679,  # stake
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
        0.0,  # revenue
        0.0,  # roundSumStakesUp
        0.0,  # roundSumStakes
        5.464642693189679,  # stake
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
        0.0,  # revenue
        0.0,  # roundSumStakesUp
        0.0,  # roundSumStakes
        3.4600000000000004,  # stake
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-1699124400-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1699124400,  # slot # Nov 04 2023 19:00:00 GMT
        "BNB/USDT",
        1699124402,  # timestamp
        7.160056238874628619,  # payout
        True,  # predictedValue
        # True,  # trueValue
        0.0,  # revenue
        0.0,  # roundSumStakesUp
        0.0,  # roundSumStakes
        3.4600000000000004,  # stake
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699300800-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1699300800,  # slot # Nov 06 2023 19:00:00 GMT
        "ETH/USDT",  # token
        1699300802,  # timestamp
        0.0,  # payout
        True,  # predictedValue
        # False,  # trueValue
        0.0,  # revenue
        0.0,  # roundSumStakesUp
        0.0,  # roundSumStakes
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
        True,
        5.0,
        10.5,
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152-1698951600",
        1698951600,
        1698951600,  # Nov 02 2023 19:00:00 GMT
        True,
        10.5,
        50.0,
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1699038000",
        1699038000,
        1699038000,  # Nov 03 2023 19:00:00 GMT
        False,
        None,
        None,
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-1699124400",
        1699124400,
        1699124400,  # Nov 04 2023 19:00:00 GMT
        True,
        5.0,
        10.5,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699214300",
        1699214300,
        1699214300,  # Nov 05 2023 19:00:00 GMT
        False,
        None,
        None,
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695-1699300800",
        1699300800,
        1699300800,  # Nov 06 2023 19:00:00 GMT
        False,
        5.5,
        10.0,
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
    payouts_df = _object_list_to_df(_payouts, payouts_schema)
    payouts_df = payouts_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return payouts_df


@pytest.fixture()
def _gql_datafactory_etl_predictions_df():
    _predictions = mock_etl_predictions()
    predictions_df = _object_list_to_df(_predictions, predictions_schema)
    predictions_df = predictions_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return predictions_df


@pytest.fixture()
def _gql_datafactory_etl_truevals_df():
    _truevals = mock_etl_truevals()
    truevals_df = _object_list_to_df(_truevals, truevals_schema)
    truevals_df = truevals_df.with_columns(
        [pl.col("timestamp").mul(1000).alias("timestamp")]
    )

    return truevals_df


@pytest.fixture()
def _gql_datafactory_etl_slots_df():
    _slots = mock_etl_slots()
    slots_df = _object_list_to_df(_slots, slots_schema)
    slots_df = slots_df.with_columns([pl.col("timestamp").mul(1000).alias("timestamp")])

    return slots_df
