from typing import Union
from enforce_typing import enforce_types


class Prediction:
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=redefined-builtin
    def __init__(
        self,
        id: str,
        pair: str,
        timeframe: str,
        prediction: Union[bool, None],  # prediction = subgraph.predicted_value
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


# =========================================================================
# utilities for testing


@enforce_types
def mock_prediction(prediction_tuple: tuple) -> Prediction:
    (
        pair_str,
        timeframe_str,
        prediction,
        stake,
        trueval,
        timestamp,
        source,
        payout,
        slot,
        user,
    ) = prediction_tuple

    _id = f"{pair_str}-{timeframe_str}-{slot}-{user}"
    return Prediction(
        id=_id,
        pair=pair_str,
        timeframe=timeframe_str,
        prediction=prediction,
        stake=stake,
        trueval=trueval,
        timestamp=timestamp,
        source=source,
        payout=payout,
        slot=slot,
        user=user,
    )
