from typing import List

from enforce_typing import enforce_types


@enforce_types
class Slot:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        timestamp: int,
        slot: int,
        trueval: bool,
        roundSumStakesUp: float,
        roundSumStakes: float,
    ) -> None:
        self.ID = ID
        self.timestamp = timestamp
        self.slot = slot
        self.trueval = trueval
        self.roundSumStakesUp = roundSumStakesUp
        self.roundSumStakes = roundSumStakes
        self.slot = slot


# =========================================================================
# utilities for testing


@enforce_types
def mock_slot(slot_tuple: tuple) -> Slot:
    (ID, timestamp, slot, trueval, roundSumStakesUp, roundSumStakes) = slot_tuple
    return Slot(
        ID=ID,
        timestamp=timestamp,
        slot=slot,
        trueval=trueval,
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
        False,
        10.5,
        2.5,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100",
        1696838100000,
        1696838100,
        False,
        2.5,
        10.5,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400000,
        1696838400,
        True,
        1.5,
        20.5,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838100",
        1696838100000,
        1696838100,
        False,
        10.5,
        2.5,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838400",
        1696838400000,
        1696838400,
        True,
        1.5,
        2.5,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838700",
        1696838700000,
        1696838700,
        True,
        10.5,
        20.5,
    ),
]
