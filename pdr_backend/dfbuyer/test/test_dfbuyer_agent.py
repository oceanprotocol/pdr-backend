from unittest.mock import MagicMock, call, patch

import pytest
from ccxt.base.exchange import math
from enforce_typing import enforce_types

from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.dfbuyer.dfbuyer_agent import WEEK, DFBuyerAgent
from pdr_backend.ppss.dfbuyer_ss import DFBuyerSS
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants import MAX_UINT, ZERO_ADDRESS
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.util.time_types import UnixTimeSeconds

PATH = "pdr_backend.dfbuyer.dfbuyer_agent"


@enforce_types
def test_dfbuyer_agent_constructor(  # pylint: disable=unused-argument
    mock_token,
    mock_ppss,
    mock_PredictoorBatcher,
):
    mock_token.return_value.allowance.return_value = 0

    agent = DFBuyerAgent(mock_ppss)

    mock_token.assert_called_with(mock_ppss.web3_pp, agent.OCEAN_addr)
    mock_token_instance = mock_token()
    mock_token_instance.approve.assert_called_with(
        agent.predictoor_batcher.contract_address, int(MAX_UINT), True
    )


@enforce_types
def test_dfbuyer_agent_constructor_empty():
    # test with no feeds
    mock_ppss_empty = MagicMock(spec=PPSS)
    mock_ppss_empty.dfbuyer_ss = MagicMock(spec=DFBuyerSS)
    mock_ppss_empty.dfbuyer_ss.filter_feeds_from_candidates.return_value = {}
    mock_ppss_empty.web3_pp = MagicMock(spec=Web3PP)
    mock_ppss_empty.web3_pp.query_feed_contracts.return_value = {}

    with pytest.raises(ValueError, match="No feeds found"):
        DFBuyerAgent(mock_ppss_empty)


@enforce_types
def test_dfbuyer_agent_get_expected_amount_per_feed(mock_dfbuyer_agent):
    ts = UnixTimeSeconds(1695211135)
    amount_per_feed_per_interval = (
        mock_dfbuyer_agent.ppss.dfbuyer_ss.amount_per_interval
        / len(mock_dfbuyer_agent.feeds)
    )
    week_start = (math.floor(ts / WEEK)) * WEEK
    time_passed = ts - week_start
    n_intervals = (
        int(time_passed / mock_dfbuyer_agent.ppss.dfbuyer_ss.consume_interval_seconds)
        + 1
    )
    expected_result = n_intervals * amount_per_feed_per_interval
    result = mock_dfbuyer_agent._get_expected_amount_per_feed(ts)
    assert result == expected_result


def test_dfbuyer_agent_get_expected_amount_per_feed_hardcoded(mock_dfbuyer_agent):
    ts = UnixTimeSeconds(1695859200)
    end = ts + WEEK - 86400  # last day
    just_before_new_week = ts + WEEK - 1  # 1 second before next week

    amount_per_feed_per_interval = (
        mock_dfbuyer_agent.ppss.dfbuyer_ss.amount_per_interval
        / len(mock_dfbuyer_agent.feeds)
    )
    result1 = mock_dfbuyer_agent._get_expected_amount_per_feed(ts)
    assert result1 == amount_per_feed_per_interval
    assert result1 * len(mock_dfbuyer_agent.feeds) == 37000 / 7  # first day

    result2 = mock_dfbuyer_agent._get_expected_amount_per_feed(end)
    assert result2 == amount_per_feed_per_interval * 7
    assert (
        result2 * len(mock_dfbuyer_agent.feeds) == 37000
    )  # last day, should distribute all

    result3 = mock_dfbuyer_agent._get_expected_amount_per_feed(just_before_new_week)
    assert result3 == amount_per_feed_per_interval * 7
    assert result3 * len(mock_dfbuyer_agent.feeds) == 37000  # still last day


@enforce_types
@patch(f"{PATH}.get_consume_so_far_per_contract")
def test_dfbuyer_agent_get_consume_so_far(mock_get_consume_so_far, mock_dfbuyer_agent):
    agent = MagicMock()
    agent.ppss.web3_pp.web3_config.owner = "0x123"
    agent.feeds = {"feed1": "0x1", "feed2": "0x2"}
    mock_get_consume_so_far.return_value = {"0x1": 10.5}
    expected_result = {"0x1": 10.5}
    result = mock_dfbuyer_agent._get_consume_so_far(0)
    assert result == expected_result


@enforce_types
@patch(f"{PATH}.PredictoorContract")
def test_dfbuyer_agent_get_prices(mock_contract, mock_dfbuyer_agent):
    mock_contract_instance = MagicMock()
    mock_contract.return_value = mock_contract_instance
    mock_contract_instance.get_price.return_value = 10000
    result = mock_dfbuyer_agent._get_prices(["0x1", "0x2"])
    assert result["0x1"] == 10000 / 1e18
    assert result["0x2"] == 10000 / 1e18


@enforce_types
def test_dfbuyer_agent_prepare_batches(mock_dfbuyer_agent):
    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    consume_times = dict(zip(addresses, [10, 30, 14, 6, 24, 16]))
    result = mock_dfbuyer_agent._prepare_batches(consume_times)

    expected_result = [
        ([addresses[0], addresses[1]], [10, 10]),
        ([addresses[1]], [20]),
        ([addresses[2], addresses[3]], [14, 6]),
        ([addresses[4]], [20]),
        ([addresses[4], addresses[5]], [4, 16]),
    ]
    assert result == expected_result


@enforce_types
def test_dfbuyer_agent_get_missing_consumes(  # pylint: disable=unused-argument
    mock_token,
    monkeypatch,
):
    ppss = MagicMock(spec=PPSS)
    ppss.web3_pp = MagicMock(spec=Web3PP)

    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    feeds = {address: MagicMock() for address in addresses}
    ppss.web3_pp.query_feed_contracts = MagicMock()
    ppss.web3_pp.query_feed_contracts.return_value = feeds
    ppss.web3_pp.OCEAN_Token.allowance.return_value = MAX_UINT

    ppss.dfbuyer_ss = MagicMock(spec=DFBuyerSS)
    ppss.dfbuyer_ss.batch_size = 3
    ppss.dfbuyer_ss.filter_feeds_from_candidates.return_value = feeds

    batcher_class = MagicMock(spec=PredictoorBatcher)
    monkeypatch.setattr(f"{PATH}.PredictoorBatcher", batcher_class)

    dfbuyer_agent = DFBuyerAgent(ppss)

    consume_amts = dict(zip(addresses, [10, 11, 32, 24, 41, 0]))
    dfbuyer_agent._get_consume_so_far = MagicMock()
    dfbuyer_agent._get_consume_so_far.return_value = consume_amts

    dfbuyer_agent._get_expected_amount_per_feed = MagicMock()
    dfbuyer_agent._get_expected_amount_per_feed.return_value = 15

    ts = 0
    result = dfbuyer_agent._get_missing_consumes(ts)
    expected_consume = dfbuyer_agent._get_expected_amount_per_feed(ts)
    expected_result = {
        address: expected_consume - consume_amts[address]
        for address in addresses
        if expected_consume - consume_amts[address] >= 0
    }
    assert result == expected_result
    dfbuyer_agent._get_consume_so_far.assert_called_once_with(ts)


@enforce_types
def test_dfbuyer_agent_get_missing_consume_times(mock_dfbuyer_agent):
    missing_consumes = {"0x1": 10.5, "0x2": 20.3, "0x3": 30.7}
    prices = {"0x1": 2.5, "0x2": 3.3, "0x3": 4.7}
    result = mock_dfbuyer_agent._get_missing_consume_times(missing_consumes, prices)
    expected_result = {"0x1": 5, "0x2": 7, "0x3": 7}
    assert result == expected_result


@enforce_types
@patch(f"{PATH}.wait_until_subgraph_syncs")
@patch("time.sleep", return_value=None)
@patch.object(DFBuyerAgent, "_get_missing_consumes")
@patch.object(DFBuyerAgent, "_get_prices")
@patch.object(DFBuyerAgent, "_get_missing_consume_times")
@patch.object(DFBuyerAgent, "_batch_txs")
@patch.object(Web3Config, "get_block")
def test_dfbuyer_agent_take_step(
    mock_get_block,
    mock_batch_txs,
    mock_get_missing_consume_times,
    mock_get_prices,
    mock_get_missing_consumes,
    mock_sleep,
    mock_subgraph_sync,  # pylint: disable=unused-argument
    mock_dfbuyer_agent,
):
    ts = 0
    mock_get_missing_consumes.return_value = {"0x1": 10.5, "0x2": 20.3, "0x3": 30.7}
    mock_get_prices.return_value = {"0x1": 2.5, "0x2": 3.3, "0x3": 4.7}
    mock_get_missing_consume_times.return_value = {"0x1": 5, "0x2": 7, "0x3": 7}
    mock_get_block.return_value = {"timestamp": 120}
    mock_batch_txs.return_value = False
    mock_dfbuyer_agent.take_step(ts)
    mock_get_missing_consumes.assert_called_once_with(ts)
    mock_get_prices.assert_called_once_with(
        list(mock_get_missing_consumes.return_value.keys())
    )
    mock_get_missing_consume_times.assert_called_once_with(
        mock_get_missing_consumes.return_value, mock_get_prices.return_value
    )
    mock_batch_txs.assert_called_once_with(mock_get_missing_consume_times.return_value)
    mock_get_block.assert_called_once_with("latest")
    mock_sleep.assert_called_once_with(86400 - 60)

    # empty feeds
    mock_dfbuyer_agent.feeds = []
    assert mock_dfbuyer_agent.take_step(ts) is None


@enforce_types
@patch.object(DFBuyerAgent, "take_step")
@patch.object(Web3Config, "get_block")
def test_dfbuyer_agent_run(mock_get_block, mock_take_step, mock_dfbuyer_agent):
    mock_get_block.return_value = {"timestamp": 0}
    mock_dfbuyer_agent.run(testing=True)
    mock_get_block.assert_called_once_with("latest")
    mock_take_step.assert_called_once_with(mock_get_block.return_value["timestamp"])

    # empty feeds
    mock_dfbuyer_agent.feeds = []
    assert mock_dfbuyer_agent.run(testing=True) is None


@enforce_types
@patch(f"{PATH}.time.sleep", return_value=None)
def test_dfbuyer_agent_consume_method(mock_sleep, mock_dfbuyer_agent):
    mock_batcher = mock_dfbuyer_agent.predictoor_batcher

    addresses_to_consume = ["0x1", "0x2"]
    times_to_consume = [2, 3]

    successful_tx = {"transactionHash": b"some_hash", "status": 1}
    failed_tx = {"transactionHash": b"some_hash", "status": 0}
    exception_tx = Exception("Error")

    mock_batcher.consume_multiple.return_value = successful_tx
    assert mock_dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

    mock_batcher.consume_multiple.return_value = failed_tx
    assert not mock_dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

    mock_batcher.consume_multiple.side_effect = exception_tx
    with pytest.raises(Exception, match="Error"):
        mock_dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

    assert mock_sleep.call_count == mock_dfbuyer_agent.ppss.dfbuyer_ss.max_request_tries


@enforce_types
def test_dfbuyer_agent_consume_batch_method(mock_dfbuyer_agent):
    addresses_to_consume = ["0x1", "0x2"]
    times_to_consume = [2, 3]

    with patch.object(
        mock_dfbuyer_agent, "_consume", side_effect=[False, True, False, False, True]
    ) as mock_consume:
        mock_dfbuyer_agent._consume_batch(addresses_to_consume, times_to_consume)
        calls = [
            call(addresses_to_consume, times_to_consume),
            call([addresses_to_consume[0]], [times_to_consume[0]]),
            call([addresses_to_consume[1]], [times_to_consume[1]]),
            call([addresses_to_consume[1]], [times_to_consume[1] // 2]),
            call(
                [addresses_to_consume[1]],
                [times_to_consume[1] // 2 + times_to_consume[1] % 2],
            ),
        ]
        mock_consume.assert_has_calls(calls)


@enforce_types
def test_dfbuyer_agent_batch_txs(mock_dfbuyer_agent):
    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    consume_times = dict(zip(addresses, [10, 30, 14, 6, 24, 16]))

    with patch.object(
        mock_dfbuyer_agent,
        "_consume_batch",
        side_effect=[False, True, False, True, True],
    ):
        failures = mock_dfbuyer_agent._batch_txs(consume_times)

    assert failures

    with patch.object(
        mock_dfbuyer_agent, "_consume_batch", side_effect=[True, True, True, True, True]
    ):
        failures = mock_dfbuyer_agent._batch_txs(consume_times)

    assert failures
