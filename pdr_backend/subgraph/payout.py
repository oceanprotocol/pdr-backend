from typing import List

from enforce_typing import enforce_types


@enforce_types
class Payout:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        # contract: str,
        token: str,
        user: str,
        slot: int,
        timestamp: int,
        payout: float,
        predictedValue: bool,
        # trueval: bool,
        revenue: float,
        roundSumStakesUp: float,
        roundSumStakes: float,
        stake: float,
    ) -> None:
        self.ID = ID
        self.user = user
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
        self.payout = payout
        self.predictedValue = predictedValue
        self.revenue = revenue
        self.roundSumStakesUp = roundSumStakesUp
        self.roundSumStakes = roundSumStakes
        self.stake = stake


@enforce_types
def mock_payout(payout_tuple: tuple) -> Payout:
    (
        ID,
        user,
        timestamp,
        token,
        slot,
        payout,
        predictedValue,
        revenue,
        roundSumStakesUp,
        roundSumStakes,
        stake,
    ) = payout_tuple

    return Payout(
        ID=ID,
        user=user,
        timestamp=timestamp,
        token=token,
        slot=slot,
        payout=payout,
        predictedValue=predictedValue,
        revenue=revenue,
        roundSumStakesUp=roundSumStakesUp,
        roundSumStakes=roundSumStakes,
        stake=stake,
    )


@enforce_types
def mock_payouts() -> List[Payout]:
    return [mock_payout(payout_tuple) for payout_tuple in _PAYOUT_TUPS]


_PAYOUT_TUPS = [
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",  # user
        1704153558,  # timestamp
        "ADA/USDT",  # token
        1704152700,  # slot
        0.0,  # payout
        True,  # predictedValue
        0.919372744934776618,  # revenue
        7.635901006590730052,  # roundSumStakesUp
        17.728238320965607921,  # roundSumStakes
        0.41,  # stake
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xfb223c3583aa934273173a55c226d598a149441c",
        "0xfb223c3583aa934273173a55c226d598a149441c",
        1704153051,
        "ADA/USDT",
        1704152700,
        3.786517720904995824,
        False,
        0.919372744934776618,
        7.635901006590730052,
        17.728238320965607921,
        2.049314196396558,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        "0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        1704153351,
        "ADA/USDT",
        1704153000,
        3.687473663992716148,
        False,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
        1.9908170679122585,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        "0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        1704153504,
        "ADA/USDT",
        1704153000,
        6.334665366356455078,
        False,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
        3.4200000000000004,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        "0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        1704153534,
        "ADA/USDT",
        1704153000,
        1.463270654801637113,
        False,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
        0.79,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        1704153558,
        "ADA/USDT",
        1704153000,
        0.0,
        True,
        0.919372744934776618,
        11.201148268567394458,
        25.423083432944667468,
        0.41,
    ),
]
