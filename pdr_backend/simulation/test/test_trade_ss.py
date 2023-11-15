from enforce_typing import enforce_types

from pdr_backend.simulation.trade_ss import TradeSS


@enforce_types
def test_trade_ss():
    ss = TradeSS(buy_amt_usd=100.0)
    assert ss.buy_amt_usd == 100.0
    assert "TradeSS" in str(ss)
