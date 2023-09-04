from unittest.mock import Mock, patch

import pytest

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
