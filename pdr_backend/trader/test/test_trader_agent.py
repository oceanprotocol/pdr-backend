import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.models.feed import mock_feed as feed_mock_feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.trader.test.trader_agent_runner import (
    mock_feed,
    mock_ppss,
    run_no_feeds,
)
from pdr_backend.trader.trader_agent import TraderAgent


@enforce_types
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_new_agent(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss()

    # agent
    agent = TraderAgent(ppss)
    assert agent.ppss == ppss
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # now try with no feeds
    run_no_feeds(TraderAgent)


@enforce_types
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_run(
    check_subscriptions_and_subscribe_mock, predictoor_contract
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss()

    # agent
    agent = TraderAgent(ppss)

    # run
    with patch.object(agent, "take_step") as ts_mock:
        agent.run(True)
    ts_mock.assert_called_once()


@enforce_types
@pytest.mark.asyncio
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
async def test_take_step(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss()
    ppss.web3_pp.set_web3_config(web3_config)

    # agent
    agent = TraderAgent(ppss)

    # Create async mock fn so we can await asyncio.gather(*tasks)
    async def _process_block_at_feed(
        addr, timestamp
    ):  # pylint: disable=unused-argument
        return (-1, [])

    agent._process_block_at_feed = Mock(side_effect=_process_block_at_feed)

    await agent.take_step()

    assert check_subscriptions_and_subscribe_mock.call_count == 2
    assert agent._process_block_at_feed.call_count == 1


@enforce_types
def custom_do_trade(feed, prediction):
    return (feed, prediction)


@pytest.mark.asyncio
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
async def test_process_block_at_feed(
    check_subscriptions_and_subscribe_mock,
):  # pylint: disable=unused-argument
    yaml_str = fast_test_yaml_str()
    ppss = PPSS(yaml_str=yaml_str, network="development")

    feed = feed_mock_feed("1m", "binance", "BTC/USDT")

    predictoor_contract = _mock_pdr_contract(feed.address)
    _inplace_mock_ppss(ppss, feed, predictoor_contract)

    # agent
    agent = TraderAgent(ppss, custom_do_trade)

    # trading
    feed_addr = feed.address
    agent.prev_traded_epochs_per_feed.clear()
    agent.prev_traded_epochs_per_feed[feed_addr] = []

    async def _do_trade(feed, prediction):  # pylint: disable=unused-argument
        pass

    agent._do_trade = Mock(side_effect=_do_trade)

    # mock feed seconds per epoch is 60
    # test agent config min buffer is 30
    # so it should trade if there's more than 30 seconds left in the epoch

    # epoch_s_left = 60 - 55 = 5, so we should not trade
    # because it's too close to the epoch end
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 55)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 0
    assert s_till_epoch_end == 5

    # epoch_s_left = 60 + 60 - 80 = 40, so we should trade
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 80)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 1
    assert s_till_epoch_end == 40

    # but not again, because we've already traded this epoch
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 80)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 1
    assert s_till_epoch_end == 40

    # but we should trade again in the next epoch
    predictoor_contract.get_current_epoch.return_value = 2
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 140)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 2
    assert s_till_epoch_end == 40

    # prediction is empty, so no trading
    predictoor_contract.get_current_epoch.return_value = 3
    predictoor_contract.get_agg_predval.side_effect = Exception(
        {"message": "An error occurred while getting agg_predval."}
    )
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 20)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 2
    assert s_till_epoch_end == 40

    # default trader
    agent = TraderAgent(ppss)
    agent.prev_traded_epochs_per_feed.clear()
    agent.prev_traded_epochs_per_feed[feed_addr] = []
    predictoor_contract.get_agg_predval.return_value = (1, 3)
    predictoor_contract.get_agg_predval.side_effect = None
    s_till_epoch_end, _ = await agent._process_block_at_feed(feed_addr, 20)
    assert len(agent.prev_traded_epochs_per_feed[feed_addr]) == 1
    assert s_till_epoch_end == 40


@enforce_types
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_save_and_load_cache(
    check_subscriptions_and_subscribe_mock,
):  # pylint: disable=unused-argument
    ppss = mock_ppss()
    feed = feed_mock_feed("1m", "binance", "BTC/USDT")

    predictoor_contract = _mock_pdr_contract(feed.address)
    _inplace_mock_ppss(ppss, feed, predictoor_contract)

    agent = TraderAgent(ppss, custom_do_trade, cache_dir=".test_cache")

    agent.prev_traded_epochs_per_feed = {
        feed.address: [1, 2, 3],
    }

    agent.update_cache()

    agent_new = TraderAgent(ppss, custom_do_trade, cache_dir=".test_cache")
    assert agent_new.prev_traded_epochs_per_feed[feed.address] == [3]
    cache_dir_path = (
        Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
        / "util/.test_cache"
    )
    for item in cache_dir_path.iterdir():
        item.unlink()
    cache_dir_path.rmdir()


@pytest.mark.asyncio
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
async def test_get_pred_properties(
    check_subscriptions_and_subscribe_mock,
    web3_config,
):  # pylint: disable=unused-argument
    ppss = mock_ppss()
    feed = feed_mock_feed("1m", "binance", "BTC/USDT")

    predictoor_contract = _mock_pdr_contract(feed.address)
    _inplace_mock_ppss(ppss, feed, predictoor_contract)

    ppss.trader_ss.set_max_tries(10)
    ppss.web3_pp.set_web3_config(web3_config)

    agent = TraderAgent(ppss)
    check_subscriptions_and_subscribe_mock.assert_called_once()

    agent.get_pred_properties = Mock()
    agent.get_pred_properties.return_value = {
        "confidence": 100.0,
        "dir": 1,
        "stake": 1,
    }

    await agent._do_trade(mock_feed(), (1.0, 1.0))
    assert agent.get_pred_properties.call_count == 1


@enforce_types
def _mock_pdr_contract(feed_address: str) -> PredictoorContract:
    c = Mock(spec=PredictoorContract)
    c.contract_address = feed_address
    c.get_agg_predval.return_value = (1, 2)
    return c


@enforce_types
def _inplace_mock_ppss(ppss: PPSS, feed: Feed, predictoor_contract: PredictoorContract):
    feeds = {feed.address: feed}

    ppss.web3_pp.query_feed_contracts = Mock()
    ppss.web3_pp.query_feed_contracts.return_value = feeds

    ppss.data_pp.filter_feeds = Mock()
    ppss.data_pp.filter_feeds.return_value = feeds

    ppss.web3_pp.get_contracts = Mock()
    ppss.web3_pp.get_contracts.return_value = {
        feed.address: predictoor_contract,
    }
