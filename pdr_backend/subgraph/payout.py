from typing import List

from enforce_typing import enforce_types


@enforce_types
class Payout:
    def __init__(
        self, ID: str, token: str, user: str, slot: int, timestamp: int, payout: float
    ) -> None:
        self.ID = ID
        self.user = user
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
        self.payout = payout


@enforce_types
def mock_payout(payout_tuple: tuple) -> Payout:
    (ID, user, timestamp, token, slot, payout) = payout_tuple

    return Payout(
        ID=ID, user=user, timestamp=timestamp, token=token, slot=slot, payout=payout
    )


@enforce_types
def mock_payouts() -> List[Payout]:
    return [mock_payout(payout_tuple) for payout_tuple in _PAYOUT_TUPS]


_PAYOUT_TUPS = [
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        1704153558000,
        "ADA/USDT",
        1704152700,
        0.0,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xfb223c3583aa934273173a55c226d598a149441c",
        "0xfb223c3583aa934273173a55c226d598a149441c",
        1704153051000,
        "ADA/USDT",
        1704152700,
        3.786517720904995824,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        "0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        1704153351000,
        "ADA/USDT",
        1704153000,
        3.687473663992716148,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        "0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        1704153504000,
        "ADA/USDT",
        1704153000,
        6.334665366356455078,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        "0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        1704153534000,
        "ADA/USDT",
        1704153000,
        1.463270654801637113,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        1704153558000,
        "ADA/USDT",
        1704153000,
        0.0,
    ),
]
