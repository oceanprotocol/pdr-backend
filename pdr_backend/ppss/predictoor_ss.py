from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class PredictoorSS(StrMixin):
    __STR_OBJDIR__ = ["d"]
    
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["predictor_ss"]

    # --------------------------------
    # yaml properties
    @property
    def s_until_epoch_end(self) -> int:
        return self.d["bot_only"]["s_until_epoch_end"]

    @property
    def stake_amount(self) -> int:
        return self.d["bot_only"]["stake_amount"]
