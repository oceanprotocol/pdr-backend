from collections import OrderedDict
from typing import Callable, List, Union

from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class Trueval(LakeMapper):
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        ID: str,
        timestamp: UnixTimeS,
        token: str,
        truevalue: Union[bool, None],
        slot: UnixTimeS,  # slot/epoch timestamp
        revenue: float,
        roundSumStakesUp: float,
        roundSumStakes: float,
    ) -> None:
        self.ID = ID
        self.truevalue = truevalue
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
        self.revenue = revenue
        self.roundSumStakesUp = roundSumStakesUp
        self.roundSumStakes = roundSumStakes

        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,
                "token": Utf8,
                "timestamp": Int64,
                "truevalue": Boolean,
                "slot": Int64,
                "revenue": Float64,
                "roundSumStakesUp": Float64,
                "roundSumStakes": Float64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "pdr_truevals"

    @staticmethod
    def get_fetch_function() -> Callable:
        # pylint: disable=import-outside-toplevel
        from pdr_backend.subgraph.subgraph_trueval import (
            fetch_truevals,
        )

        return fetch_truevals


# =========================================================================
# utilities for testing


@enforce_types
def mock_trueval(trueval_tuple: tuple) -> Trueval:
    (
        ID,
        timestamp,
        token,
        truevalue,
        slot,
        revenue,
        roundSumStakesUp,
        roundSumStakes,
    ) = trueval_tuple
    return Trueval(
        ID=ID,
        token=token,
        truevalue=truevalue,
        slot=UnixTimeS(slot),
        timestamp=UnixTimeS(timestamp),
        revenue=revenue,
        roundSumStakesUp=roundSumStakesUp,
        roundSumStakes=roundSumStakes,
    )


@enforce_types
def mock_truevals() -> List[Trueval]:
    return [mock_trueval(trueval_tuple) for trueval_tuple in _TRUEVAL_TUPS]


_TRUEVAL_TUPS = [
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400,  # Oct 09 2023
        "ETH/USDT",
        False,
        1696882021,
        0.919372744934776618,  # revenue
        7.635901006590730052,  # roundSumStakesUp
        17.728238320965607921,  # roundSumStakes
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100",
        1696838100,
        "ETH/USDT",
        True,
        1696885995,
        0.919372744934776618,  # revenue
        7.635901006590730052,  # roundSumStakesUp
        17.728238320965607921,  # roundSumStakes
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400,
        "ETH/USDT",
        True,
        1696885995,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838100",
        1696838100,
        "BTC/USDT",
        False,
        1696885995,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838400",
        1696838400,
        "BTC/USDT",
        False,
        1696885995,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838700",
        1696838700,
        "BTC/USDT",
        True,
        1696885995,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
    ),
]
