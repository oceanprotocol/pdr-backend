from collections import OrderedDict
from typing import List, Union

from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper


@enforce_types
class Slot(LakeMapper):
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        timestamp: int,
        slot: int,
        truevalue: Union[bool, None],
        roundSumStakesUp: Union[float, None],
        roundSumStakes: Union[float, None],
    ) -> None:
        self.ID = ID
        self.timestamp = timestamp
        self.slot = slot
        self.truevalue = truevalue
        self.roundSumStakesUp = roundSumStakesUp
        self.roundSumStakes = roundSumStakes
        self.slot = slot

        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,
                "timestamp": Int64,
                "slot": Int64,
                "truevalue": Boolean,
                "roundSumStakesUp": Float64,
                "roundSumStakes": Float64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "pdr_slots"


# =========================================================================
# utilities for testing


@enforce_types
def mock_slot(slot_tuple: tuple) -> Slot:
    (ID, timestamp, slot, truevalue, roundSumStakesUp, roundSumStakes) = slot_tuple
    return Slot(
        ID=ID,
        timestamp=timestamp,
        slot=slot,
        truevalue=truevalue,
        roundSumStakesUp=roundSumStakesUp,
        roundSumStakes=roundSumStakes,
    )


@enforce_types
def mock_slots() -> List[Slot]:
    return [mock_slot(slot_tuple) for slot_tuple in _SLOT_TUPS]


_SLOT_TUPS = [
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400000,
        1696838400,
        None,
        None,
        None,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100",
        1696838100000,
        1696838100,
        None,
        None,
        None,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400000,
        1696838400,
        None,
        None,
        None,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838100",
        1696838100000,
        1696838100,
        None,
        None,
        None,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838400",
        1696838400000,
        1696838400,
        None,
        None,
        None,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838700",
        1696838700000,
        1696838700,
        None,
        None,
        None,
    ),
]
