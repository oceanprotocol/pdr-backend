from enforce_typing import enforce_types

from pdr_backend.data_eng.trade_ss import TradeSS


@enforce_types
def test_trade_ss():
    ss = TradeSS("10 USDT")

    #attributes
    assert ss.buy_amt_str == "10 USDT"

    #properties
    assert ss.buy_amt_usd == 10.0

    #str
    assert "TradeSS" in str(ss)
