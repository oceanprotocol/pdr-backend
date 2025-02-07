from collections import OrderedDict
from typing import Callable, List, Union

from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class Prediction(LakeMapper):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        ID: str,
        contract: str,
        pair: str,
        timeframe: str,
        predvalue: Union[bool, None],
        stake: Union[float, None],
        truevalue: Union[bool, None],
        timestamp: UnixTimeS,  # timestamp == prediction submitted timestamp
        source: str,
        payout: Union[float, None],
        slot: UnixTimeS,  # slot/epoch timestamp
        user: str,
    ) -> None:
        self.ID = ID
        self.contract = contract
        self.pair = pair
        self.timeframe = timeframe
        self.predvalue = predvalue
        self.stake = stake
        self.truevalue = truevalue
        self.timestamp = timestamp
        self.source = source
        self.payout = payout
        self.slot = slot
        self.user = user

        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,
                "contract": Utf8,
                "pair": Utf8,
                "timeframe": Utf8,
                "predvalue": Boolean,
                "stake": Float64,
                "truevalue": Boolean,
                "timestamp": Int64,
                "source": Utf8,
                "payout": Float64,
                "slot": Int64,
                "user": Utf8,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "pdr_predictions"

    @staticmethod
    def get_fetch_function() -> Callable:
        # pylint: disable=import-outside-toplevel
        from pdr_backend.subgraph.subgraph_predictions import (
            fetch_filtered_predictions,
        )

        return fetch_filtered_predictions


# =========================================================================
# utilities for testing


@enforce_types
def mock_prediction(prediction_tuple: tuple) -> Prediction:
    (
        contract,
        pair_str,
        timeframe_str,
        predvalue,
        stake,
        truevalue,
        timestamp,
        source,
        payout,
        slot,
        user,
    ) = prediction_tuple

    ID = f"{contract}-{slot}-{user}"
    return Prediction(
        ID=ID,
        contract=contract,
        pair=pair_str,
        timeframe=timeframe_str,
        predvalue=predvalue,
        stake=stake,
        truevalue=truevalue,
        timestamp=UnixTimeS(timestamp),
        source=source,
        payout=payout,
        slot=UnixTimeS(slot),
        user=user,
    )


@enforce_types
def mock_first_predictions(multiplier: int = 1) -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in _FIRST_PREDICTION_TUPS * multiplier
    ]


@enforce_types
def mock_second_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple)
        for prediction_tuple in _SECOND_PREDICTION_TUPS
    ]


@enforce_types
def mock_daily_predictions() -> List[Prediction]:
    return [
        mock_prediction(prediction_tuple) for prediction_tuple in _DAILY_PREDICTION_TUPS
    ]


# In subgraph, timestamp will be in seconds
_FIRST_PREDICTION_TUPS = [
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        False,
        1701503000,  # Dec 02 2023
        "binance",
        0.0,
        1701503100,  # Dec 02 2023
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152",
        "BTC/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701589400,  # Dec 03 2023
        "binance",
        0.0,
        1701589500,  # Dec 03 2023
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]

_SECOND_PREDICTION_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701675800,  # Dec 04
        "binance",
        0.0500,
        1701675900,  # Dec 04
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd",
        "BTC/USDT",
        "1h",
        True,
        0.0500,
        False,
        1701503100,  # Dec 02 2023
        "binance",
        0.0,
        1701503000,  # Dec 02 2023
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701589400,  # Dec 03 2023
        "binance",
        0.0500,
        1701589500,  # Dec 03 2023
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd",
        "BNB/USDT",
        "1h",
        True,
        0.0500,
        True,
        1701675800,  # Dec 04 2023
        "kraken",
        0.0500,
        1701675900,  # Dec 04 2023
        "0xbbbb4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "1h",
        True,
        None,
        False,
        1701589400,
        "binance",
        0.0,
        1701589500,
        "0xcccc4cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1701675800,
        "binance",
        0.0500,
        1701675900,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]

_DAILY_PREDICTION_TUPS = [
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1698865200,  # Nov 01 2023 19:00:00 GMT
        "binance",
        0.0500,
        1698865200,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690",
        "BTC/USDT",
        "1h",
        True,
        0.0500,
        False,
        1698951600,  # Nov 02 2023 19:00:00 GMT
        "binance",
        0.0,
        1698951600,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
        "ADA/USDT",
        "5m",
        True,
        0.0500,
        True,
        1699038000,  # Nov 03 2023 19:00:00 GMT
        "binance",
        0.0500,
        1699038000,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd",
        "BNB/USDT",
        "1h",
        True,
        0.0500,
        True,
        1699124400,  # Nov 04 2023 19:00:00 GMT
        "kraken",
        0.0500,
        1699124400,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0xaa6515c138183303b89b98aea756b54f711710c5",
        "ETH/USDT",
        "1h",
        True,
        None,
        False,
        1699214400,  # Nov 05 2023 19:00:00 GMT
        "binance",
        0.0,
        1701589500,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
    (
        "0x30f1c55e72fe105e4a1fbecdff3145fc14177695",
        "ETH/USDT",
        "5m",
        True,
        0.0500,
        True,
        1699300800,  # Nov 06 2023 19:00:00 GMT
        "binance",
        0.0500,
        1699300800,
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
    ),
]
