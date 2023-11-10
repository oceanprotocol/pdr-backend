from enforce_typing import enforce_types
from pdr_backend.simulation.timeutil import timestr_to_ut

from pdr_backend.predictoor.base_predictoor_config import BasePredictoorConfig
from os import getenv

CAND_SIGNALS = ["open", "high", "low", "close", "volume"]
CAND_MODEL_SS = ["PREV", "LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]
CAND_EXCHANGE_IDS = ["binanceus", "binance", "kraken", "mexc3"]

@enforce_types
class PredictoorConfig4(BasePredictoorConfig):
    def __init__(self):
        super().__init__()
        self.max_N_train = 5000
        self.Nt = 10  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
        self.N_test = 10

        signals = getenv("MODEL_SIGNALS")
        if signals:
            self.signals = signals.split(",")
        else:
            self.signals = None
        assert set(self.signals).issubset(CAND_SIGNALS), f"invalid signals: {self.signals}"

        st = getenv("MODEL_ST_TIMESTAMP") # "2023-01-31" - 2019-09-13_04:00 earliest
        self.st_timestamp = timestr_to_ut(st)

        model_ss = getenv("MODEL_SS")
        self.model_ss = model_ss
        assert model_ss in CAND_MODEL_SS, f"invalid model_ss: {model_ss}"

        exchange_ids = getenv("MODEL_EXCHANGE_IDS")
        if exchange_ids:
            self.exchange_ids = exchange_ids.split(",")
        assert set(self.exchange_ids).issubset(CAND_EXCHANGE_IDS), f"invalid exchange_ids: {self.exchange_ids}"