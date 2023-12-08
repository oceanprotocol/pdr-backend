from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.trader.test.trader_agent_runner import (
    mock_feed,
    mock_ppss,
    run_no_feeds,
)
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1


@enforce_types
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_new_agent(  # pylint: disable=unused-argument
    check_subscriptions_and_subscribe_mock, predictoor_contract
):
    # params
    ppss = mock_ppss()

    # agent
    agent = TraderAgent1(ppss)
    assert agent.ppss == ppss
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # now try with no feeds
    run_no_feeds(TraderAgent1)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
async def test_do_trade(  # pylint: disable=unused-argument
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):
    # params
    ppss = mock_ppss()
    ppss.web3_pp.set_web3_config(web3_config)

    # agent
    agent = TraderAgent1(ppss)
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # trading
    agent.exchange = Mock()
    agent.exchange.create_market_buy_order.return_value = {"info": {"origQty": 1}}

    await agent._do_trade(mock_feed(), (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1
