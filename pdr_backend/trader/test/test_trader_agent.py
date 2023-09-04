from unittest.mock import patch
from pdr_backend.trader.trader_agent import TraderAgent
from pdr_backend.trader.trader_config import TraderConfig
from pdr_backend.trader.trader_agent import get_trader


def test_new_agent():
    trader_config = TraderConfig()
    agent = TraderAgent(trader_config, get_trader)
    assert agent.config == trader_config


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
