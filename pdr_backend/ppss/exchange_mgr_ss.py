from typing import Optional, Union

from enforce_typing import enforce_types
import numpy as np

from pdr_backend.exchange.ccxtutil import CCXTExchangeMixin
from pdr_backend.util.strutil import StrMixin


class ExchangeMgrSS(StrMixin, CCXTExchangeMixin):
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

        # check timeout
        timeout = d["timeout"]
        if not isinstance(timeout, (int, float)):
            raise TypeError(timeout)
        if timeout < 0 or np.isinf(timeout):
            raise ValueError(timeout)

        # check ccxt_params
        ccxt_params = d["ccxt_params"]
        if not isinstance(ccxt_params, dict):
            raise TypeError(ccxt_params)
        for key in ccxt_params.keys():
            if not isinstance(key, str):
                raise TypeError(ccxt_params)

        # check dydx_params
        dydx_params = d["dydx_params"] or {}
        if not isinstance(dydx_params, dict):
            raise TypeError(dydx_params)
        for key in dydx_params.keys():
            if not isinstance(key, str):
                raise TypeError(dydx_params)

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
def exchange_mgr_ss_test_dict(
    timeout: Optional[Union[int, float]] = None,
    ccxt_params: Optional[dict] = None,
    dydx_params: Optional[dict] = None,
) -> dict:
    """Use this function's return dict 'd' to construct ExchangeMgrSS(d)"""
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
