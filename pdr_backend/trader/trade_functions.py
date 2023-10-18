from abc import ABC, abstractmethod
from enum import Enum
from typing import Tuple

from pdr_backend.models.feed import Feed


class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BaseStrategy(ABC):
    @abstractmethod
    def determine_action(
        self, feed: Feed, prediction: Tuple[float, float]
    ) -> Tuple[TradeAction, float]:
        pass


class SimpleThresholdStrategy(BaseStrategy):
    def __init__(self, buy_threshold=0.6, sell_threshold=0.4):
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def determine_action(
        self, feed: Feed, prediction: Tuple[float, float]
    ) -> Tuple[TradeAction, float]:
        pred_nom, pred_denom = prediction
        probability_up = pred_nom / pred_denom

        if probability_up > self.buy_threshold:
            return TradeAction.BUY, probability_up
        elif probability_up < self.sell_threshold:
            return TradeAction.SELL, 1 - probability_up
        else:
            return TradeAction.HOLD, 0


def execute_action(feed: Feed, confidence: float, action: TradeAction):
    """
    do trade here
    """
    pass


async def do_trade(feed: Feed, prediction: Tuple[float, float]):
    """
    @description
        This function is called each time there's a new prediction available.
        By default, it prints the signal.
        The user should implement their trading algorithm here.
    @params
        feed : Feed
            An instance of the Feed object.

        prediction : Tuple[float, float]
            A tuple containing two float values, the unit is ETH:
            - prediction[0]: Amount staked for the price going up.
            - prediction[1]: Total stake amount.
    @note
        The probability of the price going up is determined by dividing
        prediction[0] by prediction[1]. The magnitude of stake amounts indicates
        the confidence of the prediction. Ensure stake amounts
        are sufficiently large to be considered meaningful.
    """
    pred_nom, pred_denom = prediction
    print(f"      {feed} has a new prediction: {pred_nom} / {pred_denom}.")
    # Trade here
    # ...

    strategy = SimpleThresholdStrategy(buy_threshold=0.6, sell_threshold=0.4)
    action, confidence = strategy.determine_action(feed, prediction)
