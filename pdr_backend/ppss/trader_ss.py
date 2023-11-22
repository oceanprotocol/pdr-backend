from typing import Union

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class TraderSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["data_pp"]

    # --------------------------------
    # yaml properties: sim only
    @property
    def buy_amt_str(self) -> Union[int, float]:
        """How much to buy. Eg 10."""
        return self.d["sim_only"]["buy_amt"]

    # --------------------------------
    # yaml properties: bot only
    @property
    def min_buffer(self) -> int:
        """Only trade if there's > this time left. Denominated in s."""
        return self.d["bot_only"]["min_buffer"]

    @property
    def max_tries(self) -> int:
        """Max no. attempts to process a feed. Eg 10"""
        return self.d["bot_only"]["max_tries"]

    @property
    def position_size(self) -> Union[int, float]:
        """Trading size. Eg 10"""
        return self.d["bot_only"]["position_size"]

    # --------------------------------
    # setters (add as needed)
    @enforce_types
    def set_max_tries(self, max_tries):
        self.d["bot_only"]["max_tries"] = max_tries

    @enforce_types
    def set_min_buffer(self, min_buffer):
        self.d["bot_only"]["min_buffer"] = min_buffer

    @enforce_types
    def set_position_size(self, position_size):
        self.d["bot_only"]["position_size"] = position_size

    # --------------------------------
    # derivative properties
    @property
    def buy_amt_usd(self):
        amt_s, _ = self.buy_amt_str.split()
        return float(amt_s)
