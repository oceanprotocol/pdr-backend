# pylint: disable=redefined-outer-name

import pytest

from unittest.mock import Mock

from pdr_backend.ppss.exchange_mgr_ss import ExchangeMgrSS
from pdr_backend.sim.sim_trader import SimTrader

FEE_PERCENT = 0.01


@pytest.fixture
def mock_ppss():
    ppss = Mock()
    ppss.trader_ss.take_profit = 0.05
    ppss.trader_ss.stop_loss = 0.05
    ppss.trader_ss.buy_amt_usd.amt_eth = 1000
    ppss.trader_ss.fee_percent = FEE_PERCENT
    ppss.sim_ss.tradetype = "histmock"
    ppss.exchange_mgr_ss = Mock(spec=ExchangeMgrSS)
    ppss.predictoor_ss.exchange_str = "mock"
    return ppss


@pytest.fixture
def mock_predict_feed():
    predict_feed = Mock()
    predict_feed.pair.base_str = "ETH"
    predict_feed.pair.quote_str = "USDT"
    return predict_feed


@pytest.fixture
def sim_trader(mock_ppss, mock_predict_feed):
    return SimTrader(mock_ppss, mock_predict_feed)


def test_initial_state(sim_trader):
    assert sim_trader.position_open == ""
    assert sim_trader.position_size == 0
    assert sim_trader.position_worth == 0
    assert sim_trader.tp == 0.0
    assert sim_trader.sl == 0.0


def test_close_long_position(sim_trader):
    sim_trader.position_open = "long"
    sim_trader.position_size = 10
    sim_trader.position_worth = 1000
    sim_trader._sell = Mock(return_value=1100)
    profit = sim_trader.close_long_position(110)
    assert profit == 100
    assert sim_trader.position_open == ""


def test_close_short_position(sim_trader):
    sim_trader.position_open = "short"
    sim_trader.position_size = 10
    sim_trader.position_worth = 1000
    sim_trader._buy = Mock()
    profit = sim_trader.close_short_position(90)
    assert profit == 100
    assert sim_trader.position_open == ""


def test_trade_iter_open_long(sim_trader):
    sim_trader._buy = Mock(return_value=10)
    sim_trader.trade_iter(100, True, False, 0.5, 0, 110, 90)
    assert sim_trader.position_open == "long"
    assert sim_trader.position_worth == 1500
    assert sim_trader.position_size == 10


def test_trade_iter_open_short(sim_trader):
    sim_trader._sell = Mock(return_value=1500)
    sim_trader.trade_iter(100, False, True, 0, 0.5, 110, 90)
    assert sim_trader.position_open == "short"
    assert sim_trader.position_worth == 1500
    assert sim_trader.position_size == 15


def test_trade_iter_close_long_take_profit(sim_trader):
    sim_trader.position_open = "long"
    sim_trader.position_size = 10
    sim_trader.position_worth = 1000
    sim_trader.tp = 110
    sim_trader._sell = Mock(return_value=1100)
    profit = sim_trader.trade_iter(100, False, False, 0, 0, 110, 90)
    assert profit == 100  # 1100 - 1000
    assert sim_trader.position_open == ""


def test_trade_iter_close_short_stop_loss(sim_trader):
    sim_trader.position_open = "short"
    sim_trader.position_size = 10
    sim_trader.position_worth = 1000
    sim_trader.sl = 110
    sim_trader._buy = Mock()
    profit = sim_trader.trade_iter(100, False, False, 0, 0, 110, 90)
    assert profit == -100  # 1100 - 1000
    assert sim_trader.position_open == ""


def test_buy(sim_trader):
    sim_trader.exchange.create_market_buy_order = Mock()
    tokcoin_amt_recd = sim_trader._buy(100.0, 1000.0)
    assert tokcoin_amt_recd == (1000 / 100) * (1 - FEE_PERCENT)
    sim_trader.exchange.create_market_buy_order.assert_called_once()


def test_sell(sim_trader):
    sim_trader.exchange.create_market_sell_order = Mock()
    usdcoin_amt_recd = sim_trader._sell(100.0, 10.0)
    assert usdcoin_amt_recd == (100 * 10) * (1 - FEE_PERCENT)
    sim_trader.exchange.create_market_sell_order.assert_called_once()
