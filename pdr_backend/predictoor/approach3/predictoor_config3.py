from enforce_typing import enforce_types
from pdr_backend.simulation.timeutil import timestr_to_ut

from pdr_backend.predictoor.base_predictoor_config import BasePredictoorConfig


@enforce_types
class PredictoorConfig3(BasePredictoorConfig):
    def __init__(self):
        super().__init__()
        self.max_N_train = 5000
        self.Nt = 10  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
        self.N_test = 10
        self.signals = ["close"]  # ["open", "high","low", "close", "volume"]
        self.st_timestamp = timestr_to_ut("2023-01-31")  # 2019-09-13_04:00 earliest
        self.model_ss = "LIN"  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR
