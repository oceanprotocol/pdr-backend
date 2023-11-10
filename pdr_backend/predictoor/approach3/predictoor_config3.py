from enforce_typing import enforce_types
from pdr_backend.simulation.timeutil import timestr_to_ut

from pdr_backend.predictoor.base_predictoor_config import BasePredictoorConfig
from os import getenv

CAND_SIGNALS = ["open", "high", "low", "close", "volume"]
CAND_MODEL_SS = ["PREV", "LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]
CAND_EXCHANGE_IDS = ["binanceus", "binance", "kraken", "mexc3"]

@enforce_types
class PredictoorConfig3(BasePredictoorConfig):
    def __init__(self):
        super().__init__()
        self.max_N_train = 5000
        self.Nt = 10  # eg 10. model inputs Nt past pts z[t-1], .., z[t-Nt]
        self.N_test = 10
        
        # Read valid signals from environment variable
        signals = getenv("MODEL_SIGNALS")
        self.signals = signals.split(",") if signals else ["close"]
        assert set(self.signals).issubset(CAND_SIGNALS), f"Invalid signals: {self.signals}"

        # Read valid start time from environment variable
        st = getenv("MODEL_ST_TIMESTAMP")  # "2023-01-31"
        self.st_timestamp = timestr_to_ut(st) if st else timestr_to_ut("2023-01-31")
        # assert self.st_timestamp > 2019-09-13_04:00 earliest

        # Read valid model from environment variable
        model_ss = getenv("MODEL_SS")  # PREV, LIN, GPR, SVR, NuSVR, LinearSVR
        self.model_ss = model_ss if model_ss else "LIN"
        assert model_ss in CAND_MODEL_SS, f"Invalid model_ss: {self.model_ss}"

        # Read valid exchange IDs from environment variable
        exchange_ids = getenv("MODEL_EXCHANGE_IDS")
        self.exchange_ids = exchange_ids.split(",") if exchange_ids else ["binanceus"]
        assert set(self.exchange_ids).issubset(CAND_EXCHANGE_IDS), f"Invalid exchange_ids: {self.exchange_ids}"