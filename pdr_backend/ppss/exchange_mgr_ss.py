from typing import Union

from enforce_typing import enforce_types

from pdr_backend.util.ccxtutil import CCXTExchangeMixin
from pdr_backend.util.strutil import StrMixin


class ExchangemgrSS(StrMixin, CCXTExchangeMixin):
    """
    This ss has parameters across all exchange APIs (ccxt, dydx, ..).
    It's used by ExchangeMgr.

    It explicitly does *not* hold an exchange name, because
    - that's passed into ExchangeMgr.exchange() -> does't need it
    - and it would violate DRY, since trader_ss & sim_ss have it via "feed"
    """

    __STR_OBJDIR__ = ["d"]

    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["exchange_ss"]

    # --------------------------------
    # yaml properties
    @property
    def timeout(self) -> Union[int, float]:
        return self.d["timeout"]

    @property
    def ccxt_params(self) -> dict:
        return self.d["ccxt_params"]

    @property
    def dydx_params(self) -> dict:
        return self.d["dydx_params"]


# =========================================================
# utilities for testing


@enforce_types
def exchangemgr_ss_test_dict(
    timeout: Optional[Union[int, float]] = None,
    ccxt_params: Optional[dict] = None,
    dydx_params: Optional[dict] = None,
) -> dict:
    """Use this function's return dict 'd' to construct ExchangemgrSS(d)"""
    d = {
        "timeout": timeout or 30,
        "ccxt_params": ccxt_params
        or {
            "createMarketBuyOrderRequiresPrice": False,
            "defaultType": "spot",
        },
        "dydx_params": dydx_params or {},
    }
    return d
