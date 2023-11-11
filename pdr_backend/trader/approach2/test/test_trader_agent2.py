from datetime import datetime
from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.trader.approach2.trader_agent2 import TraderAgent2
from pdr_backend.trader.approach2.trader_config2 import TraderConfig2


@enforce_types
def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.address = "0xtestfeed"
    feed.seconds_per_epoch = 60
    return feed


@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_new_agent(check_subscriptions_and_subscribe_mock, predictoor_contract):
    # Setting up the mock trader configuration
    trader_config = Mock(spec=TraderConfig2)
    trader_config.exchange_id = "mexc3"
    trader_config.exchange_pair = "BTC/USDT"
    trader_config.timeframe = "5m"
    trader_config.size = 10.0
    trader_config.get_feeds = Mock()
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    trader_config.get_contracts = Mock()
    trader_config.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }

    # Creating a new agent and asserting the configuration
    agent = TraderAgent2(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # Setting up a configuration with no feeds and testing for SystemExit
    no_feeds_config = Mock(spec=TraderConfig2)
    no_feeds_config.get_feeds.return_value = {}
    no_feeds_config.max_tries = 10

    with pytest.raises(SystemExit):
        TraderAgent2(no_feeds_config)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
async def test_do_trade(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):
    # Mocking the trader configuration
    trader_config = Mock(spec=TraderConfig2)
    trader_config.exchange_id = "mexc3"
    trader_config.exchange_pair = "BTC/USDT"
    trader_config.timeframe = "5m"
    trader_config.size = 10.0
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    trader_config.get_contracts = Mock()
    trader_config.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }
    trader_config.max_tries = 10
    trader_config.web3_config = web3_config

    # Creating a new agent and setting up the mock objects
    agent = TraderAgent2(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # Creating mock objects and functions
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

    # Performing a trade and checking the call counts of the methods
    await agent._do_trade(mock_feed(), (1.0, 1.0))

    assert agent.get_pred_properties.call_count == 1
    assert agent.exchange.create_market_buy_order.call_count == 1
    assert agent.update_positions.call_count == 1
    assert agent.portfolio.open_position.call_count == 1
    assert agent.update_cache.call_count == 1


# Test for TraderAgent2.update_positions
@enforce_types
@patch.object(TraderAgent2, "check_subscriptions_and_subscribe")
def test_update_positions(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):
    trader_config = Mock(spec=TraderConfig2)
    trader_config.exchange_id = "mexc3"
    trader_config.exchange_pair = "BTC/USDT"
    trader_config.timeframe = "5m"
    trader_config.size = 10.0
    trader_config.get_feeds = Mock()
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    trader_config.get_contracts = Mock()
    trader_config.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }
    trader_config.max_tries = 10
    trader_config.web3_config = web3_config

    # Creating a new agent and setting up the mock objects
    agent = TraderAgent2(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

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
def test_should_close(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):
    trader_config = Mock(spec=TraderConfig2)
    trader_config.exchange_id = "mexc3"
    trader_config.exchange_pair = "BTC/USDT"
    trader_config.timeframe = "5m"
    trader_config.size = 10.0
    trader_config.get_feeds = Mock()
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    trader_config.get_contracts = Mock()
    trader_config.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }
    trader_config.max_tries = 10
    trader_config.web3_config = web3_config

    # TraderConfig2.timedelta is a property, so we need to mock it
    trader_config.timedelta = 300

    # Creating a new agent and setting up the mock objects
    agent = TraderAgent2(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # Test 1 - Creating mock objects and functions to handle should_close
    mock_order = Mock()
    mock_order.timestamp = 1

    result = agent.should_close(mock_order)
    assert result

    # Test 2 - Make more order recent, now it should not close
    mock_order.timestamp = datetime.now().timestamp() * 1000

    result = agent.should_close(mock_order)
    assert not result
