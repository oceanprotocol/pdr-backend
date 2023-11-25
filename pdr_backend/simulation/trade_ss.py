from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class TradeSS(StrMixin):
    """User-controllable parameters, at trading level"""

    def __init__(self, buy_amt_usd: float):
        self.buy_amt_usd = buy_amt_usd
