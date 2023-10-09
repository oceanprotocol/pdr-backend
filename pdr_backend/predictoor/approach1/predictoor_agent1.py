import random
from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.predictoor.approach1.predictoor_config1 import PredictoorConfig1


@enforce_types
class PredictoorAgent1(BasePredictoorAgent):
    predictoor_config_class = PredictoorConfig1

    def get_prediction(
        self, addr: str, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair. Info in self.feeds[addr]
          timestamp -- int -- when to make prediction for (unix time)

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
