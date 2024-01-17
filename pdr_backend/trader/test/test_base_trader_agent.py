import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import mock_feed_ppss
from pdr_backend.ppss.web3_pp import (
    inplace_mock_feedgetters,
    inplace_mock_w3_and_contract_with_tracking,
)
from pdr_backend.trader.base_trader_agent import BaseTraderAgent
from pdr_backend.trader.test.trader_agent_runner import (
    INIT_BLOCK_NUMBER,
    INIT_TIMESTAMP,
    do_constructor,
    do_run,
    setup_take_step,
)


@enforce_types
@patch.object(BaseTraderAgent, "check_subscriptions_and_subscribe")
def test_trader_agent_constructor(check_subscriptions_and_subscribe_mock):
    do_constructor(BaseTraderAgent, check_subscriptions_and_subscribe_mock)


@enforce_types
@patch.object(BaseTraderAgent, "check_subscriptions_and_subscribe")
def test_trader_agent_run(check_subscriptions_and_subscribe_mock):
    do_run(BaseTraderAgent, check_subscriptions_and_subscribe_mock)


@enforce_types
@pytest.mark.asyncio
@patch.object(BaseTraderAgent, "check_subscriptions_and_subscribe")
async def test_trader_agent_take_step(
    check_subscriptions_and_subscribe_mock,
    monkeypatch,
):
    agent = setup_take_step(
        BaseTraderAgent,
        check_subscriptions_and_subscribe_mock,
        monkeypatch,
    )

    await agent.take_step()

    assert check_subscriptions_and_subscribe_mock.call_count == 2
    assert agent._process_block.call_count == 1


@enforce_types
def custom_do_trade(feed, prediction):
    return (feed, prediction)


@pytest.mark.asyncio
@patch.object(BaseTraderAgent, "check_subscriptions_and_subscribe")
async def test_process_block(  # pylint: disable=unused-argument
    check_subscriptions_and_subscribe_mock,
    monkeypatch,
):
    feed, ppss = mock_feed_ppss("1m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds
    _mock_pdr_contract = inplace_mock_w3_and_contract_with_tracking(
        ppss.web3_pp,
        INIT_TIMESTAMP,
        INIT_BLOCK_NUMBER,
        ppss.trader_ss.timeframe_s,
        feed.address,
        monkeypatch,
    )

    agent = BaseTraderAgent(ppss, custom_do_trade)

    agent.prev_traded_epochs = []

    async def _do_trade(feed, prediction):  # pylint: disable=unused-argument
        pass

    agent._do_trade = Mock(side_effect=_do_trade)

    # mock feed seconds per epoch is 60
    # test agent config min buffer is 30
    # so it should trade if there's more than 30 seconds left in the epoch

    # epoch_s_left = 60 - 55 = 5, so we should not trade
    # because it's too close to the epoch end
    s_till_epoch_end = await agent._process_block(55)
    assert len(agent.prev_traded_epochs) == 0
    assert s_till_epoch_end == 5

    # epoch_s_left = 60 + 60 - 80 = 40, so we should trade
    s_till_epoch_end = await agent._process_block(80)
    assert len(agent.prev_traded_epochs) == 1
    assert s_till_epoch_end == 40

    # but not again, because we've already traded this epoch
    s_till_epoch_end = await agent._process_block(80)
    assert len(agent.prev_traded_epochs) == 1
    assert s_till_epoch_end == 40

    # but we should trade again in the next epoch
    _mock_pdr_contract.get_current_epoch = Mock()
    _mock_pdr_contract.get_current_epoch.return_value = 2
    s_till_epoch_end = await agent._process_block(140)
    assert len(agent.prev_traded_epochs) == 2
    assert s_till_epoch_end == 40


@enforce_types
@patch.object(BaseTraderAgent, "check_subscriptions_and_subscribe")
def test_save_and_load_cache(
    check_subscriptions_and_subscribe_mock,
):  # pylint: disable=unused-argument
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    inplace_mock_feedgetters(ppss.web3_pp, feed)  # mock publishing feeds

    agent = BaseTraderAgent(ppss, custom_do_trade, cache_dir=".test_cache")

    agent.prev_traded_epochs = [1, 2, 3]

    agent.update_cache()

    agent_new = BaseTraderAgent(ppss, custom_do_trade, cache_dir=".test_cache")
    assert agent_new.prev_traded_epochs == [3]
    cache_dir_path = (
        Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
        / "util/.test_cache"
    )
    for item in cache_dir_path.iterdir():
        item.unlink()
    cache_dir_path.rmdir()
