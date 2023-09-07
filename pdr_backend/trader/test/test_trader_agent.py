from unittest.mock import Mock, patch

import pytest

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.trader_agent import TraderAgent, get_trader
from pdr_backend.trader.trader_config import TraderConfig


def test_new_agent(predictoor_contract):
    trader_config = TraderConfig()
    trader_config.get_feeds = Mock()
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": ""
    }
    trader_config.get_contracts = Mock()
    trader_config.get_contracts.return_value = {
        "0x0000000000000000000000000000000000000000": predictoor_contract
    }
    agent = TraderAgent(trader_config, get_trader)
    assert agent.config == trader_config

    no_feeds_config = Mock(spec=TraderConfig)
    no_feeds_config.get_feeds.return_value = {}

    with pytest.raises(SystemExit):
        TraderAgent(no_feeds_config, get_trader)


def test_run():
    trader_config = Mock(spec=TraderConfig)
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": ""
    }
    agent = TraderAgent(trader_config, get_trader)

    with patch.object(agent, "take_step") as ts_mock:
        agent.run(True)

    ts_mock.assert_called_once()


def test_take_step(web3_config):
    trader_config = Mock(spec=TraderConfig)
    trader_config.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": ""
    }
    trader_config.web3_config = web3_config
    agent = TraderAgent(trader_config, get_trader)

    with patch.object(agent, "_process_block_at_feed") as ts_mock:
        agent.take_step()

    assert ts_mock.call_count > 0


def custom_trader(feed, prediction):
    return (feed, prediction)


def test_process_block_at_feed():
    trader_config = Mock(spec=TraderConfig)
    trader_config.trader_min_buffer = 20
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.address = "0x123"

    feed.seconds_per_epoch = 60
    predictoor_contract = Mock(spec=PredictoorContract)
    predictoor_contract.get_agg_predval.return_value = (1, 2)

    trader_config.get_feeds.return_value = {"0x123": feed}
    trader_config.get_contracts.return_value = {"0x123": predictoor_contract}

    agent = TraderAgent(trader_config, custom_trader)

    # epoch_s_left = 60 - 55 = 5, so we should not trade
    # because it's too close to the epoch end
    agent._process_block_at_feed("0x123", 55)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 0

    # epoch_s_left = 60 + 60 - 80 = 40, so we should not trade
    agent._process_block_at_feed("0x123", 80)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1

    # but not again, because we've already traded this epoch
    agent._process_block_at_feed("0x123", 80)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1

    # but we should trade again in the next epoch
    predictoor_contract.get_current_epoch.return_value = 2
    agent._process_block_at_feed("0x123", 20)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 2

    # prediction is empty, so no trading
    predictoor_contract.get_current_epoch.return_value = 3
    predictoor_contract.get_agg_predval.side_effect = Exception(
        "An error occurred while getting agg_predval."
    )
    agent._process_block_at_feed("0x123", 20)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 2

    # default trader
    agent = TraderAgent(trader_config)
    predictoor_contract.get_agg_predval.return_value = (1, 3)
    predictoor_contract.get_agg_predval.side_effect = None
    agent._process_block_at_feed("0x123", 20)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1


def test_save_and_load_cache():
    trader_config = Mock(spec=TraderConfig)
    trader_config.trader_min_buffer = 20
    feed = Mock(spec=Feed)
    feed.name = "test feed"
    feed.seconds_per_epoch = 60
    predictoor_contract = Mock(spec=PredictoorContract)
    predictoor_contract.get_agg_predval.return_value = (1, 2)

    trader_config.get_feeds.return_value = {"0x1": feed, "0x2": feed, "0x3": feed}
    trader_config.get_contracts.return_value = {
        "0x1": predictoor_contract,
        "0x2": predictoor_contract,
        "0x3": predictoor_contract,
    }

    agent = TraderAgent(trader_config, custom_trader, cache_dir=".test_cache")

    agent.prev_traded_epochs_per_feed = {
        "0x1": [1, 2, 3],
        "0x2": [4, 5, 6],
        "0x3": [1, 24, 66],
    }

    print(agent.prev_traded_epochs_per_feed)
    agent.save_previous_epochs()

    agent_new = TraderAgent(trader_config, custom_trader, cache_dir=".test_cache")
    print(agent_new.prev_traded_epochs_per_feed)
    assert agent_new.prev_traded_epochs_per_feed["0x1"] == [3]
    assert agent_new.prev_traded_epochs_per_feed["0x2"] == [6]
    assert agent_new.prev_traded_epochs_per_feed["0x3"] == [66]
