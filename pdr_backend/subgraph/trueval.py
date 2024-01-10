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
        trueval: Union[bool, None],
        slot: int,  # slot/epoch timestamp
    ) -> None:
        self.ID = ID
        self.trueval = trueval
        self.timestamp = timestamp
        self.token = token
        self.slot = slot


# =========================================================================
# utilities for testing


@enforce_types
def mock_trueval(trueval_tuple: tuple) -> Trueval:
    (ID, timestamp, token, slot, trueval) = trueval_tuple
    return Trueval(
        ID=ID,
        token=token,
        slot=slot,
        trueval=trueval,
        timestamp=timestamp,
    )


@enforce_types
def mock_truevals() -> List[Trueval]:
    return [mock_truevals(subscription_tuple) for subscription_tuple in _TRUEVAL_TUPS]


_TRUEVAL_TUPS = [
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400" "ETH/USDT",
        1696838400,
        False,
        1696882021,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100" "ETH/USDT",
        1696838100,
        True,
        1696885995,
    ),
    (
        "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400" "ETH/USDT",
        1696838400,
        True,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838100" "BTC/USDT",
        1696838100,
        False,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838400" "BTC/USDT",
        1696838400,
        False,
        1696885995,
    ),
    (
        "0xe66421fd29fc2d27d0724f161f01b8cbdcd69690-1696838700" "BTC/USDT",
        1696838700,
        True,
        1696885995,
    ),
]
