import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.approach1.trader_config1 import TraderConfig1
from pdr_backend.util.contract import get_address


def mock_feed():
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.seconds_per_epoch = 60
    return feed


@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_new_agent(check_subscriptions_and_subscribe_mock, predictoor_contract):
    trader_config = Mock(spec=TraderConfig1)
    trader_config.exchange_id = "mexc3"
    trader_config.pair = "BTC/USDT"
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


@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
@patch.object(TraderAgent1, "do_trade")
@patch.object(TraderAgent1, "get_pred_properties")
async def test_take_step(
    check_subscriptions_and_subscribe_mock,
    do_trade_mock,
    get_pred_properties_mock,
    predictoor_contract,
    web3_config,
):
    trader_config = Mock(spec=TraderConfig1)
    trader_config.exchange_id = "mexc3"
    trader_config.pair = "BTC/USDT"
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

    print("trader_config.get_feeds", trader_config.get_feeds())
    print("trader_config.get_contracts", trader_config.get_contracts())

    agent = TraderAgent1(trader_config)
    assert agent.config == trader_config
    check_subscriptions_and_subscribe_mock.assert_called_once()

    with patch.object(agent, "_process_block_at_feed") as ts_mock:
        await agent.take_step()

    assert ts_mock.call_count > 0
    do_trade_mock.assert_called_once()
    get_pred_properties_mock.assert_called_once()
