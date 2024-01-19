from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_feed_ppss
from pdr_backend.ppss.web3_pp import (
    inplace_mock_feedgetters,
    inplace_mock_w3_and_contract_with_tracking,
)

INIT_TIMESTAMP = 107
INIT_BLOCK_NUMBER = 13


@enforce_types
def do_constructor(agent_class, check_subscriptions_and_subscribe_mock):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    # 1 predict feed
    assert ppss.trader_ss.feed
    agent = agent_class(ppss)
    assert agent.ppss == ppss
    assert agent.feed
    check_subscriptions_and_subscribe_mock.assert_called_once()


@enforce_types
def do_run(  # pylint: disable=unused-argument
    agent_class,
    check_subscriptions_and_subscribe_mock,
):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    agent = agent_class(ppss)

    with patch.object(agent, "take_step") as mock_stake_step:
        agent.run(True)
    mock_stake_step.assert_called_once()


@enforce_types
def setup_take_step(  # pylint: disable=unused-argument
    agent_class,
    check_subscriptions_and_subscribe_mock,
    monkeypatch,
):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds
    _mock_feed_contract = inplace_mock_w3_and_contract_with_tracking(
        ppss.web3_pp,
        INIT_TIMESTAMP,
        INIT_BLOCK_NUMBER,
        ppss.trader_ss.timeframe_s,
        feed.address,
        monkeypatch,
    )

    agent = agent_class(ppss)

    # Create async mock fn so we can await asyncio.gather(*tasks)
    async def _process_block(timestamp):  # pylint: disable=unused-argument
        return -1

    agent._process_block = Mock(side_effect=_process_block)

    return agent


@enforce_types
def setup_trade(  # pylint: disable=unused-argument
    agent_class, check_subscriptions_and_subscribe_mock
):
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    agent = agent_class(ppss)

    agent.exchange = Mock()
    agent.exchange.create_market_buy_order.return_value = {"info": {"origQty": 1}}

    return agent, feed
