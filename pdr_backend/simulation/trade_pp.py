from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


@enforce_types
class TradePP(StrMixin):
    """User-uncontrollable parameters, at trading level"""

    def __init__(
        self,
        fee_percent: float,  # Eg 0.001 is 0.1%. Trading fee (simulated)
        init_holdings: dict,  # Eg {"USDT": 100000.00}
    ):
        self.fee_percent = fee_percent
        self.init_holdings = init_holdings
