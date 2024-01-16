from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_feed_ppss
from pdr_backend.ppss.web3_pp import inplace_mock_feedgetters
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trader.test.trader_agent_runner import (
    do_constructor,
    do_run,
    setup_trade,
)


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_trader_agent2_constructor(check_subscriptions_and_subscribe_mock):
    do_constructor(TraderAgent2, check_subscriptions_and_subscribe_mock)


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_trader_agent2_run(check_subscriptions_and_subscribe_mock):
    do_run(TraderAgent2, check_subscriptions_and_subscribe_mock)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
async def test_trader_agent2_do_trade(check_subscriptions_and_subscribe_mock):
    agent, feed = setup_trade(
        TraderAgent2,
        check_subscriptions_and_subscribe_mock,
    )

    await agent._do_trade(feed, (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_trader_agent2_update_positions(  # pylint: disable=unused-argument
    check_subscriptions_and_subscribe_mock,
):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    agent = TraderAgent2(ppss)

    agent.exchange = Mock()
    agent.exchange.create_market_sell_order.return_value = {"info": {"origQty": 1}}

    agent.portfolio = Mock()
    mock_sheet = Mock()
    mock_sheet.open_positions = [Mock(), Mock()]
    agent.portfolio.get_sheet.return_value = mock_sheet
    agent.should_close = Mock()
    agent.should_close.return_value = True

    agent.close_position = Mock()
    agent.update_cache = Mock()

    agent.update_positions()

    assert agent.portfolio.get_sheet.call_count == 1
    assert agent.exchange.create_market_sell_order.call_count == 2
    assert agent.portfolio.close_position.call_count == 2
    assert agent.portfolio.close_position.call_args == (
        (feed.address, {"info": {"origQty": 1}}),
    )
    assert agent.update_cache.call_count == 2

    original_call_count = agent.update_cache.call_count

    # does nothing without sheet
    agent.portfolio = Mock()
    mock_sheet = None
    agent.portfolio.get_sheet.return_value = mock_sheet
    agent.update_positions()
    assert agent.update_cache.call_count == original_call_count

    # does nothing without a portfolio
    agent.portfolio = None
    agent.update_positions()
    assert agent.update_cache.call_count == original_call_count


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_trader_agent2_should_close(  # pylint: disable=unused-argument
    check_subscriptions_and_subscribe_mock,
):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    agent = TraderAgent2(ppss)

    # test 1 - creating mock objects and functions to handle should_close
    mock_order = Mock()
    mock_order.timestamp = 1

    result = agent.should_close(mock_order)
    assert result

    # test 2 - ensure more order recent, now it should not close
    mock_order.timestamp = datetime.now().timestamp() * 1000

    result = agent.should_close(mock_order)
    assert not result


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
async def test_trader_agent2_do_trade_edges(
    check_subscriptions_and_subscribe_mock, capfd
):
    agent, feed = setup_trade(
        TraderAgent2,
        check_subscriptions_and_subscribe_mock,
    )

    await agent._do_trade(feed, (1.0, 0))
    out, _ = capfd.readouterr()
    assert "There's no stake on this" in out
