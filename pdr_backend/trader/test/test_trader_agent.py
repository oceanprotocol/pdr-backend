from unittest.mock import Mock, patch

import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.trader_agent import TraderAgent, get_trader
from pdr_backend.trader.trader_config import TraderConfig


def test_new_agent():
    trader_config = TraderConfig()
    agent = TraderAgent(trader_config, get_trader)
    assert agent.config == trader_config

    no_feeds_config = Mock(spec=TraderConfig)
    no_feeds_config.get_feeds.return_value = {}

    with pytest.raises(SystemExit):
        TraderAgent(no_feeds_config, get_trader)


def test_run():
    trader_config = TraderConfig()
    agent = TraderAgent(trader_config, get_trader)

    with patch.object(agent, "take_step") as ts_mock:
        agent.run(True)

    ts_mock.assert_called_once()


def test_take_step():
    trader_config = TraderConfig()
    agent = TraderAgent(trader_config, get_trader)

    with patch.object(agent, "_process_block_at_feed") as ts_mock:
        agent.take_step()

    assert ts_mock.call_count == len(agent.feeds)


class MyMockClass(Mock):
    def __gt__(self, intval):
        return self.val > intval


def test_process_block_at_feed():
    trader_config = Mock(spec=TraderConfig)
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.address = "0x123"

    feed.seconds_per_epoch = 60
    predictoor_contract = MyMockClass(spec=PredictoorContract)
    predictoor_contract.get_current_epoch.return_value = 1

    trader_config.s_until_epoch_end = 10
    trader_config.get_feeds.return_value = {"0x123": feed}
    trader_config.get_contracts.return_value = {"0x123": predictoor_contract}

    agent = TraderAgent(trader_config, get_trader)

    # epoch_s_left = 60 + 60 - 10 = 110, so we should not trade
    agent._process_block_at_feed("0x123", 1)
    assert predictoor_contract.get_agg_predval.call_count == 0

    feed.seconds_per_epoch = 10
    trader_config.s_until_epoch_end = 20
    # epoch_s_left = 19, so we should trade
    agent._process_block_at_feed("0x123", 1)
    assert predictoor_contract.get_agg_predval.call_count == 1
