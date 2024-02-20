from unittest.mock import patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1
from pdr_backend.trader.test.trader_agent_runner import (
    do_constructor,
    do_run,
    setup_trade,
)


@enforce_types
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_trader_agent1_constructor(check_subscriptions_and_subscribe_mock):
    do_constructor(TraderAgent1, check_subscriptions_and_subscribe_mock)


@enforce_types
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_trader_agent1_run(check_subscriptions_and_subscribe_mock):
    do_run(TraderAgent1, check_subscriptions_and_subscribe_mock)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
async def test_trader_agent1_do_trade(check_subscriptions_and_subscribe_mock, caplog):
    agent, feed = setup_trade(
        TraderAgent1,
        check_subscriptions_and_subscribe_mock,
    )

    await agent._do_trade(feed, (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1

    await agent._do_trade(feed, (1.0, 0))
    assert "There's no stake on this" in caplog.text

    agent.order = {}
    with patch.object(agent.exchange, "create_market_sell_order", return_value="mock"):
        await agent._do_trade(feed, (1.0, 1.0))

    assert "Closing Order" in caplog.text
