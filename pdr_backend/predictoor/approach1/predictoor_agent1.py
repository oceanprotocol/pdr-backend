import random
from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class PredictoorAgent1(BasePredictoorAgent):
    def get_one_sided_prediction(
        self, timestamp: UnixTimeS  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Predict for a given timestamp.

        @arguments
          timestamp -- UnixTimeSeonds -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of Eth

        @notes
          Below is the default implementation, giving random predictions.
          You need to customize it to implement your own strategy.
        """
        # Pick random prediction & random stake. You need to customize this.
        predval = bool(random.getrandbits(1))

        # Stake amount is in ETH
        stake = random.randint(1, 30) / 10000

        return (predval, stake)

    def get_two_sided_prediction(
        self, timestamp: UnixTimeS  # pylint: disable=unused-argument
    ) -> Tuple[float, float]:
        raise NotImplementedError("Two-sided prediction not implemented")