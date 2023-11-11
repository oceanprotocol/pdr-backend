from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach1.trader_config1 import TraderConfig1


@enforce_types
def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.seconds_per_epoch = 60
    return feed


@enforce_types
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_new_agent(check_subscriptions_and_subscribe_mock, predictoor_contract):
    trader_config = Mock(spec=TraderConfig1)
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
    agent = TraderAgent1(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    no_feeds_config = Mock(spec=TraderConfig1)
    no_feeds_config.get_feeds.return_value = {}
    no_feeds_config.max_tries = 10

    with pytest.raises(SystemExit):
        TraderAgent1(no_feeds_config)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
async def test_do_trade(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):
    trader_config = Mock(spec=TraderConfig1)
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

    agent = TraderAgent1(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    agent.exchange = Mock()
    agent.exchange.create_market_buy_order.return_value = {"info": {"origQty": 1}}

    await agent._do_trade(mock_feed(), (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1
