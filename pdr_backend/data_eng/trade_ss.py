from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class TradeSS(StrMixin):
    """User-controllable parameters, at trading level"""

    @enforce_types
    def __init__(self, buy_amt_str: str):
        self.buy_amt_str = buy_amt_str # e.g. '10 USDT'

    @property
    def buy_amt_usd(self):
        amt_s, token = self.buy_amt_str.split()
        return float(amt_s)
