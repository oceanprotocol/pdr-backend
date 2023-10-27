"""
## About SECONDS_TILL_EPOCH_END

If we want to predict the value for epoch E, we need to do it in epoch E - 2
(latest.  Though we could predict for a distant future epoch if desired)

And to do so, our tx needs to be confirmed in the last block of epoch
(otherwise, it's going to be part of next epoch and our prediction tx
 will revert)

But, for every prediction, there are several steps. Each takes time:
- time to compute prediction (e.g. run model inference)
- time to generate the tx
- time until your pending tx in mempool is picked by miner
- time until your tx is confirmed in a block

To help, you can set envvar `SECONDS_TILL_EPOCH_END`. It controls how many
seconds in advance of the epoch ending you want the prediction process to
start. A predictoor can submit multiple predictions. However, only the final
submission made before the deadline is considered valid.

To clarify further: if this value is set to 60, the predictoor will be asked
to predict in every block during the last 60 seconds before the epoch
concludes.
"""

from abc import ABC
from os import getenv

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig


@enforce_types
class BasePredictoorConfig(BaseConfig, ABC):
    def __init__(self):
        super().__init__()
        self.s_until_epoch_end = int(getenv("SECONDS_TILL_EPOCH_END", "60"))

        # For approach 1 stake amount is randomly determined this has no effect.
        # For approach 2 stake amount is determined by:
        #   `STAKE_AMOUNT * confidence` where confidence is between 0 and 1.
        # For approach 3 this is the stake amount.
        self.stake_amount = float(getenv("STAKE_AMOUNT", "1"))  # stake amount in eth
