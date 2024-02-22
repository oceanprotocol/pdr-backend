from typing import Union, List

from enforce_typing import enforce_types


@enforce_types
class Trueval:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        timestamp: int,
        token: str,
        truevalue: Union[bool, None],
        slot: int,  # slot/epoch timestamp
    ) -> None:
        self.ID = ID
        self.truevalue = truevalue
        self.timestamp = timestamp
        self.token = token
        self.slot = slot


# =========================================================================
# utilities for testing


@enforce_types
def mock_trueval(trueval_tuple: tuple) -> Trueval:
    (ID, timestamp, token, truevalue, slot) = trueval_tuple
    return Trueval(
        ID=ID,
        token=token,
        slot=slot,
        truevalue=truevalue,
        timestamp=timestamp,
    )


@enforce_types
def mock_truevals() -> List[Trueval]:
    return [mock_trueval(trueval_tuple) for trueval_tuple in _TRUEVAL_TUPS]


_TRUEVAL_TUPS = [
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400,
        "ETH/USDT",
        False,
        1696882021,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100",
        1696838100,
        "ETH/USDT",
        True,
        1696885995,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400",
        1696838400,
        "ETH/USDT",
        True,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838100",
        1696838100,
        "BTC/USDT",
        False,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838400",
        1696838400,
        "BTC/USDT",
        False,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838700",
        1696838700,
        "BTC/USDT",
        True,
        1696885995,
    ),
]
