from typing import Union


class Prediction:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=redefined-builtin
    def __init__(
        self,
        id: str,
        pair: str,
        timeframe: str,
        prediction: Union[bool, None],
        stake: Union[float, None],
        trueval: Union[bool, None],
        timestamp: int,  # timestamp == prediction submitted timestamp
        source: str,
        payout: Union[float, None],
        slot: int,  # slot/epoch timestamp
        user: str,
    ) -> None:
        self.id = id
        self.pair = pair
        self.timeframe = timeframe
        self.prediction = prediction
        self.stake = stake
        self.trueval = trueval
        self.timestamp = timestamp
        self.source = source
        self.payout = payout
        self.slot = slot
        self.user = user
