from typing import Tuple

from enforce_typing import enforce_types

from pdr_backend.predictoor.base_predictoor_agent import BasePredictoorAgent
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class PredictoorAgent1(BasePredictoorAgent):
    def get_prediction(
        self, timestamp: UnixTimeS  # pylint: disable=unused-argument
    ) -> Tuple[float, float]:
        """
        @description
          Predict for a given timestamp.

        @arguments
          timestamp -- UnixTimeS -- when to make prediction for (unix time)

        @return
          stake_up -- amt to stake up, in units of Eth
          stake_down -- amt to stake down, ""
        
        @notes
          Here, it allocates equal stake to up vs down (50-50).
          You need to customize this to implement your own strategy.
        """
        stake_amt = self.ppss.predictoor_ss.stake_amount
        stake_up, stake_down = 0.50 * stake_amt, 0.50 * stake_amt
        return (stake_up, stake_down)
    
