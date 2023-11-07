from enforce_typing import enforce_types

from pdr_backend.simulation.tradeutil import (
    pairstr,
    pairstr_to_coin,
    pairstr_to_usdcoin,
    TradeParams,
    TradeSS,
)


@enforce_types
def test_TradeParams():
    pp = TradeParams(
        fee_percent=0.01,
        init_holdings={"USDT": 10000.0, "BTC": 0.0},
    )
    assert pp.fee_percent == 0.01
    assert "TradeParams" in str(pp)
    assert "fee_percent" in str(pp)


@enforce_types
def test_TradeSS(tmpdir):
    ss = TradeSS(
        do_plot=False,
        logpath=str(tmpdir),
        buy_amt_usd=100000.00,
    )
    assert ss.buy_amt_usd == 100000.00
    assert "TradeSS" in str(ss)
    assert "buy_amt_usd" in str(ss)


@enforce_types
def test_pairstr():
    assert pairstr("BTC", "USDT") == "BTC/USDT"
    assert pairstr_to_coin("BTC/USDT") == "BTC"
    assert pairstr_to_usdcoin("BTC/USDT") == "USDT"
