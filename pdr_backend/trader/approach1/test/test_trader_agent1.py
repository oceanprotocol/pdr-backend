from unittest.mock import patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.trader.test.trader_agent_runner import (
    do_constructor,
    do_run,
    setup_trade,
)
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1


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
async def test_trader_agent1_do_trade(check_subscriptions_and_subscribe_mock):
    agent, feed = setup_trade(
        TraderAgent1,
        check_subscriptions_and_subscribe_mock,
    )

    await agent._do_trade(feed, (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1
