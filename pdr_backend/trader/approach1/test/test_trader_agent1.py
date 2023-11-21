from unittest.mock import Mock, patch

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.models.feed import Feed
from pdr_backend.trader.test.trader_agent_runner import mock_feed, mock_ppss
from pdr_backend.trader.approach1.trader_agent1 import TraderAgent1


@enforce_types
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
def test_new_agent(
        check_subscriptions_and_subscribe_mock, predictoor_contract, tmpdir):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)

    # agent
    agent = TraderAgent1(ppss)
    assert agent.ppss == ppss
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # now try with no feeds
    run_no_feeds(tmpdir, TraderAgent1)


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent1, "check_subscriptions_and_subscribe")
async def test_do_trade(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
    tmpdir,
):
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)
    ppss.web3_pp.set_web3_config(web3_config)

    # agent
    agent = TraderAgent1(ppss)
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # trading
    agent.exchange = Mock()
    agent.exchange.create_market_buy_order.return_value = {"info": {"origQty": 1}}

    await agent._do_trade(mock_feed(), (1.0, 1.0))
    assert agent.exchange.create_market_buy_order.call_count == 1
