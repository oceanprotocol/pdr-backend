import ccxt
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.exchange.mock_exchange import MockExchange


@enforce_types
def test_exchange_mgr_main():
    d = exchangemgr_ss_test_dict()
    mgr = ExchangeMgr(d)

    assert isinstance(mgr.exchange("mock"), MockExchange)
    assert isinstance(mgr.exchange("binance"), ccxt.binance.binance)
    assert isinstance(mgr.exchange("binanceus"), ccxt.binanceus.binanceus)
    assert isinstance(mgr.exchange("kraken"), ccxt.kraken.kraken)

    with pytest.raises(NotImplementedError):
        mgr.exchange("dydx")

    with pytest.raises(AttributeError):
        mgr.exchange("foo")


@enforce_types
def test_exchange_mgr_ss():
    d = exchangemgr_ss_test_dict()
    d["ccxt_params"]["createMarketBuyOrderRequiresPrice"] = True
    d["ccxt_params"]["defaultType"] = "spot"
    mgr = ExchangeMgr(d)
    assert mgr.ss.ccxt_params["createMarketBuyOrderRequiresPrice"]
    assert mgr.ss.ccxt_params["defaultType"] == "spot"


@enforce_types
def test_exchange_mgr_binance():
    d = exchangemgr_ss_test_dict()
    mgr = ExchangeMgr(d)

    exchange = mgr.exchange("binance")

    # basic test of api: just grab current price
    # - full docs at https://docs.ccxt.com/#/?id=price-tickers
    ticker = exchange.fetchTicker("BTC/USDT")
    assert ticker["symbol"] == "BTC/USDT"
    assert ticker["close"] > 0
