import ccxt
import pytest
from enforce_typing import enforce_types

from pdr_backend.exchange.dydx_exchange import DydxExchange
from pdr_backend.exchange.mock_exchange import MockExchange
from pdr_backend.exchange.exchange_mgr import ExchangeMgr
from pdr_backend.ppss.exchange_mgr_ss import exchange_mgr_ss_test_dict, ExchangeMgrSS


@enforce_types
def test_exchange_mgr_main():
    d = exchange_mgr_ss_test_dict()
    mgr = ExchangeMgr(ExchangeMgrSS(d))

    assert isinstance(mgr.exchange("mock"), MockExchange)
    assert isinstance(mgr.exchange("binance"), ccxt.binance)
    assert isinstance(mgr.exchange("binanceus"), ccxt.binanceus)
    assert isinstance(mgr.exchange("kraken"), ccxt.kraken)
    assert isinstance(mgr.exchange("dydx"), DydxExchange)

    with pytest.raises(AttributeError):
        mgr.exchange("foo")


@enforce_types
def test_exchange_mgr_ss():
    d = exchange_mgr_ss_test_dict()
    d["ccxt_params"]["createMarketBuyOrderRequiresPrice"] = True
    d["ccxt_params"]["defaultType"] = "spot"
    mgr = ExchangeMgr(ExchangeMgrSS(d))
    assert mgr.ss.ccxt_params["createMarketBuyOrderRequiresPrice"]
    assert mgr.ss.ccxt_params["defaultType"] == "spot"


@enforce_types
def test_exchange_mgr_binanceus():
    d = exchange_mgr_ss_test_dict()
    mgr = ExchangeMgr(ExchangeMgrSS(d))

    exchange = mgr.exchange("binanceus")

    # basic test of api: just grab current price
    # - full docs at https://docs.ccxt.com/#/?id=price-tickers
    ticker = exchange.fetchTicker("BTC/USDT")
    assert ticker["symbol"] == "BTC/USDT"
    assert ticker["close"] > 0
