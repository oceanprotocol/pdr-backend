import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.trader.test.trader_agent_runner import (
    mock_feed,
    mock_ppss,
    run_no_feeds,
)
from pdr_backend.trader.trader_agent import TraderAgent


@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_new_agent(
    check_subscriptions_and_subscribe_mock, predictoor_contract, tmpdir
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)

    # agent
    agent = TraderAgent(ppss)
    assert agent.ppss == ppss
    check_subscriptions_and_subscribe_mock.assert_called_once()

    # now try with no feeds
    run_no_feeds(tmpdir, TraderAgent)


@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_run(
    check_subscriptions_and_subscribe_mock, predictoor_contract, tmpdir
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)

    # agent
    agent = TraderAgent(ppss)

    # run
    with patch.object(agent, "take_step") as ts_mock:
        agent.run(True)
    ts_mock.assert_called_once()


@pytest.mark.asyncio
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
async def test_take_step(
    check_subscriptions_and_subscribe_mock,
    predictoor_contract,
    web3_config,
    tmpdir,
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss(predictoor_contract, tmpdir)
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


def custom_trader(feed, prediction):
    return (feed, prediction)


@pytest.mark.asyncio
@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
async def test_process_block_at_feed(
    check_subscriptions_and_subscribe_mock, tmpdir
):  # pylint: disable=unused-argument
    feed = mock_feed()

    predictoor_contract = Mock(spec=PredictoorContract)
    predictoor_contract.get_agg_predval.return_value = (1, 2)

    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")

    ppss.web3_pp.get_feeds.return_value = {"0x123": feed}
    ppss.web3_pp.get_contracts.return_value = {"0x123": predictoor_contract}

    # agent
    agent = TraderAgent(ppss, custom_trader)
    agent.prev_traded_epochs_per_feed.clear()
    agent.prev_traded_epochs_per_feed["0x123"] = []

    async def _do_trade(feed, prediction):  # pylint: disable=unused-argument
        pass

    agent._do_trade = Mock(side_effect=_do_trade)

    # epoch_s_left = 60 - 55 = 5, so we should not trade
    # because it's too close to the epoch end
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 55)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 0
    assert s_till_epoch_end == 5

    # epoch_s_left = 60 + 60 - 80 = 40, so we should not trade
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 80)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1
    assert s_till_epoch_end == 40

    # but not again, because we've already traded this epoch
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 80)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1
    assert s_till_epoch_end == 40

    # but we should trade again in the next epoch
    predictoor_contract.get_current_epoch.return_value = 2
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 140)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 2
    assert s_till_epoch_end == 40

    # prediction is empty, so no trading
    predictoor_contract.get_current_epoch.return_value = 3
    predictoor_contract.get_agg_predval.side_effect = Exception(
        {"message": "An error occurred while getting agg_predval."}
    )
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 20)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 2
    assert s_till_epoch_end == 40

    # default trader
    agent = TraderAgent(ppss)
    agent.prev_traded_epochs_per_feed.clear()
    agent.prev_traded_epochs_per_feed["0x123"] = []
    predictoor_contract.get_agg_predval.return_value = (1, 3)
    predictoor_contract.get_agg_predval.side_effect = None
    s_till_epoch_end, _ = await agent._process_block_at_feed("0x123", 20)
    assert len(agent.prev_traded_epochs_per_feed["0x123"]) == 1
    assert s_till_epoch_end == 40


@patch.object(TraderAgent, "check_subscriptions_and_subscribe")
def test_save_and_load_cache(
    check_subscriptions_and_subscribe_mock,
    tmpdir,
):  # pylint: disable=unused-argument
    feed = mock_feed()

    predictoor_contract = Mock(spec=PredictoorContract)
    predictoor_contract.get_agg_predval.return_value = (1, 2)

    ppss = mock_ppss(predictoor_contract, tmpdir)

    ppss.web3_pp.get_feeds.return_value = {"0x1": feed, "0x2": feed, "0x3": feed}
    ppss.web3_pp.get_contracts.return_value = {
        "0x1": predictoor_contract,
        "0x2": predictoor_contract,
        "0x3": predictoor_contract,
    }

    agent = TraderAgent(ppss, custom_trader, cache_dir=".test_cache")

    agent.prev_traded_epochs_per_feed = {
        "0x1": [1, 2, 3],
        "0x2": [4, 5, 6],
        "0x3": [1, 24, 66],
    }

    agent.update_cache()

    agent_new = TraderAgent(ppss, custom_trader, cache_dir=".test_cache")
    assert agent_new.prev_traded_epochs_per_feed["0x1"] == [3]
    assert agent_new.prev_traded_epochs_per_feed["0x2"] == [6]
    assert agent_new.prev_traded_epochs_per_feed["0x3"] == [66]
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
    tmpdir,
):  # pylint: disable=unused-argument
    # params
    ppss = mock_ppss(None, tmpdir)

    ppss.web3_pp.get_feeds.return_value = {
        "0x0000000000000000000000000000000000000000": mock_feed()
    }
    ppss.trader_ss.set_max_tries(10)
    ppss.web3_pp.web3_config = web3_config
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
