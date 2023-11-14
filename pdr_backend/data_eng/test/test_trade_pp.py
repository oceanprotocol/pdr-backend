from enforce_typing import enforce_types

from pdr_backend.data_eng.trade_pp import TradePP


@enforce_types
def test_trade_pp():
    pp = TradePP(
        fee_percent=0.01,
        init_holdings_strs = ['10000.0 USDT', '0 BTC'],
    )

    # attributes
    assert pp.fee_percent == 0.01
    assert pp.init_holdings_strs == ['10000.0 USDT', '0 BTC']

    # properties
    assert pp.init_holdings["USDT"] == 10000.0
    assert "TradePP" in str(pp)
    assert "fee_percent" in str(pp)
