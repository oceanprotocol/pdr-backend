from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class TraderPP(StrMixin):

    @enforce_types
    def __init__(self, d: dict):
        self.d = d # yaml_dict["trader_pp"]

    # --------------------------------
    # yaml properties
    @property
    def fee_percent(self) -> str:
        return self.d["sim_only"]["fee_percent"] # Eg 0.001 is 0.1%.Trading fee
    
    @property
    def init_holdings_strs(self) -> List[str]:
        return self.d["sim_only"]["init_holdings"] # eg ["1000 USDT", ..]

    # --------------------------------
    # derivative properties
    @property
    def init_holdings(self) -> Dict[str, float]:
        d = {}
        for s in self.init_holdings_strs:
            amt_s, coin = s.split()
            amt = float(amt_s)
            d[coin] = amt
        return d
