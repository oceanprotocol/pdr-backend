from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class TradePP(StrMixin):
    """User-uncontrollable parameters, at trading level"""

    @enforce_types
    def __init__(
        self,
        fee_percent: float,  # Eg 0.001 is 0.1%. Trading fee (simulated)
        init_holdings_strs: List[str],  # Eg {"USDT": 100000.00}
    ):
        self.fee_percent:float = fee_percent
        self.init_holdings_strs = init_holdings_strs

    @property
    def init_holdings(self) -> Dict[str, float]:
        d = {}
        for s in self.init_holdings_strs:
            amt_s, coin = s.split()
            amt = float(amt_s)
            d[coin] = amt
        return d
