from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class PayoutSS(StrMixin):
    __STR_OBJDIR__ = ["d"]
    
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["payout_ss"]

    # --------------------------------
    # yaml properties
    @property
    def batch_size(self) -> int:
        return self.d["batch_size"]
    
    # --------------------------------
    # setters
    def set_batch_size(self, batch_size: int):
        self.d["batch_size"] = batch_size
