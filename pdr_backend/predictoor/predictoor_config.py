from os import getenv

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig


@enforce_types
class PredictoorConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.s_until_epochs_end = int(getenv("SECONDS_TILL_EPOCH_END", "60"))
        self.stake_amount = int(getenv("STAKE_AMOUNT", "1"))
        self.get_prediction = None # child needs to set this prediction function
