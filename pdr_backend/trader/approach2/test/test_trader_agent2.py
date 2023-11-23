from datetime import datetime
from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.trader.test.trader_agent_runner import (
    mock_feed,
    mock_ppss,
    run_no_feeds,
)
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_new_agent(check_subscriptions_and_subscribe_mock, predictoor_contract, tmpdir):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)

    # agent
    agent = TraderAgent2(ppss)
    assert agent.ppss == ppss
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # when no feeds
    run_no_feeds(tmpdir, TraderAgent2)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
async def test_do_trade(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
    tmpdir,
):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)
    ppss.web3_pp.set_web3_config(web3_config)

    # agent
    agent = TraderAgent2(ppss)
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # trading: mock objects and functions
    agent.exchange = Mock()
    agent.exchange.create_market_buy_order.return_value = {"info": {"origQty": 1}}

    agent.portfolio = Mock()
    agent.update_positions = Mock()
    agent.update_cache = Mock()

    agent.get_pred_properties = Mock()
    agent.get_pred_properties.return_value = {
        "confidence": 100.0,
        "dir": 1,
        "stake": 1,
    }

    # trading: doing a trade and checking the call counts of the methods
    await agent._do_trade(mock_feed(), (1.0, 1.0))

    assert agent.get_pred_properties.call_count == 1
    assert agent.exchange.create_market_buy_order.call_count == 1
    assert agent.update_positions.call_count == 1
    assert agent.portfolio.open_position.call_count == 1
    assert agent.update_cache.call_count == 1


# Test for TraderAgent2.update_positions
@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_update_positions(predictoor_contract, web3_config, tmpdir):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)
    ppss.web3_pp.set_web3_config(web3_config)

    # agent
    agent = TraderAgent2(ppss)

    # Creating mock objects and functions
    agent.exchange = Mock()
    agent.exchange.create_market_sell_order.return_value = {"info": {"origQty": 1}}

    agent.feeds = Mock()
    agent.feeds.keys.return_value = ["0x0000000000000000000000000000000000000000"]
    agent.portfolio = Mock()
    mock_sheet = Mock()
    mock_sheet.open_positions = [Mock(), Mock()]
    agent.portfolio.get_sheet.return_value = mock_sheet
    agent.should_close = Mock()
    agent.should_close.return_value = True

    agent.close_position = Mock()
    agent.update_cache = Mock()

    # Update agent positions
    agent.update_positions()

    assert agent.portfolio.get_sheet.call_count == 1
    assert agent.exchange.create_market_sell_order.call_count == 2
    assert agent.portfolio.close_position.call_count == 2
    assert agent.portfolio.close_position.call_args == (
        ("0x0000000000000000000000000000000000000000", {"info": {"origQty": 1}}),
    )
    assert agent.update_cache.call_count == 2


# Test for TraderAgent2.should_close
@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_should_close(predictoor_contract, web3_config, tmpdir):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)
    ppss.web3_pp.set_web3_config(web3_config)
    ppss.data_pp.set_timeframe(300)

    # agent
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
