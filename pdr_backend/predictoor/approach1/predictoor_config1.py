from enforce_typing import enforce_types

from pdr_backend.predictoor.predictoor_config import PredictoorConfig

@enforce_types
class PredictoorConfig1(PredictoorConfig):
    def __init__(self):
        super().__init__()
        self.get_prediction = get_prediction
