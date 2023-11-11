from enforce_typing import enforce_types

from pdr_backend.util.pairutil import (
    pairstr,
    pairstr_to_coin,
    pairstr_to_usdcoin,
)


@enforce_types
def test_pairutil():
    assert pairstr("BTC", "USDT") == "BTC/USDT"
    assert pairstr_to_coin("BTC/USDT") == "BTC"
    assert pairstr_to_usdcoin("BTC/USDT") == "USDT"
