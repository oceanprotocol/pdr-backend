from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class TraderSS(StrMixin):

    @enforce_types
    def __init__(self, d: dict):
        self.d = d # yaml_dict["data_pp"]

    # --------------------------------
    # yaml properties
    @property
    def buy_amt_str(self) -> str:
        return self.d["sim_only"]["buy_amt"] # eg "1m"

    # --------------------------------
    # derivative properties
    @property
    def buy_amt_usd(self):
        amt_s, token = self.buy_amt_str.split()
        return float(amt_s)
