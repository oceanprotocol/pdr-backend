from unittest.mock import MagicMock, call, patch

from ccxt.base.exchange import math
import pytest
from pdr_backend.dfbuyer.dfbuyer_agent import WEEK, DFBuyerAgent
from pdr_backend.util.constants import MAX_UINT, ZERO_ADDRESS
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.dfbuyer.dfbuyer_agent.Token")
@patch("pdr_backend.dfbuyer.dfbuyer_agent.get_address")
def test_new_agent(mock_get_address, mock_token, dfbuyer_config):
    mock_get_address.return_value = ZERO_ADDRESS
    mock_token_instance = MagicMock()
    mock_token.return_value = mock_token_instance
    agent = DFBuyerAgent(dfbuyer_config)

    assert len(mock_get_address.call_args_list) == 2
    call1 = mock_get_address.call_args_list[0]
    assert call1 == call(dfbuyer_config.web3_config.w3.eth.chain_id, "PredictoorHelper")
    call2 = mock_get_address.call_args_list[1]
    assert call2 == call(dfbuyer_config.web3_config.w3.eth.chain_id, "Ocean")

    mock_token.assert_called_with(dfbuyer_config.web3_config, agent.token_addr)
    mock_token_instance.approve.assert_called_with(
        agent.predictoor_batcher.contract_address, int(MAX_UINT), True
    )


def test_get_expected_amount_per_feed(dfbuyer_agent):
    ts = 1695211135
    amount_per_feed_per_interval = dfbuyer_agent.config.amount_per_interval / len(
        dfbuyer_agent.feeds
    )
    week_start = (math.floor(ts / WEEK)) * WEEK
    time_passed = ts - week_start
    n_intervals = int(time_passed / dfbuyer_agent.config.consume_interval_seconds) + 1
    expected_result = n_intervals * amount_per_feed_per_interval
    result = dfbuyer_agent._get_expected_amount_per_feed(ts)
    assert result == expected_result


def test_get_expected_amount_per_feed_hardcoded(dfbuyer_agent):
    ts = 16958592000
    end = ts + WEEK - 86400  # last day
    just_before_new_week = ts + WEEK - 1  # 1 second before next week

    amount_per_feed_per_interval = dfbuyer_agent.config.amount_per_interval / len(
        dfbuyer_agent.feeds
    )
    result1 = dfbuyer_agent._get_expected_amount_per_feed(ts)
    assert result1 == amount_per_feed_per_interval
    assert result1 * len(dfbuyer_agent.feeds) == 37000 / 7  # first day

    result2 = dfbuyer_agent._get_expected_amount_per_feed(end)
    assert result2 == amount_per_feed_per_interval * 7
    assert (
        result2 * len(dfbuyer_agent.feeds) == 37000
    )  # last day, should distribute all

    result3 = dfbuyer_agent._get_expected_amount_per_feed(just_before_new_week)
    assert result3 == amount_per_feed_per_interval * 7
    assert result3 * len(dfbuyer_agent.feeds) == 37000  # still last day


@patch("pdr_backend.dfbuyer.dfbuyer_agent.get_consume_so_far_per_contract")
def test_get_consume_so_far(mock_get_consume_so_far, dfbuyer_agent):
    agent = MagicMock()
    agent.config.web3_config.owner = "0x123"
    agent.feeds = {"feed1": "0x1", "feed2": "0x2"}
    mock_get_consume_so_far.return_value = {"0x1": 10.5}
    expected_result = {"0x1": 10.5}
    result = dfbuyer_agent._get_consume_so_far(0)
    assert result == expected_result


@patch("pdr_backend.dfbuyer.dfbuyer_agent.PredictoorContract")
def test_get_prices(mock_contract, dfbuyer_agent):
    mock_contract_instance = MagicMock()
    mock_contract.return_value = mock_contract_instance
    mock_contract_instance.get_price.return_value = 10000
    result = dfbuyer_agent._get_prices(["0x1", "0x2"])
    assert result["0x1"] == 10000 / 1e18
    assert result["0x2"] == 10000 / 1e18


def test_prepare_batches(dfbuyer_agent):
    dfbuyer_agent.config.batch_size = 10

    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    consume_times = dict(zip(addresses, [5, 15, 7, 3, 12, 8]))
    result = dfbuyer_agent._prepare_batches(consume_times)

    expected_result = [
        ([addresses[0], addresses[1]], [5, 5]),
        ([addresses[1]], [10]),
        ([addresses[2], addresses[3]], [7, 3]),
        ([addresses[4]], [10]),
        ([addresses[4], addresses[5]], [2, 8]),
    ]
    assert result == expected_result


@patch.object(DFBuyerAgent, "_get_consume_so_far")
@patch.object(DFBuyerAgent, "_get_expected_amount_per_feed")
def test_get_missing_consumes(
    mock_get_expected_amount_per_feed, mock_get_consume_so_far, dfbuyer_agent
):
    ts = 0
    addresses = [ZERO_ADDRESS[: -len(str(i))] + str(i) for i in range(1, 7)]
    consume_amts = {
        addresses[0]: 10,
        addresses[1]: 11,
        addresses[2]: 32,
        addresses[3]: 24,
        addresses[4]: 41,
        addresses[5]: 0,
    }
    mock_get_consume_so_far.return_value = consume_amts
    mock_get_expected_amount_per_feed.return_value = 15
    result = dfbuyer_agent._get_missing_consumes(ts)
    expected_consume = dfbuyer_agent._get_expected_amount_per_feed(ts)
    expected_result = {
        address: expected_consume - consume_amts[address]
        for address in addresses
        if expected_consume - consume_amts[address] >= 0
    }
    assert result == expected_result
    mock_get_consume_so_far.assert_called_once_with(ts)


def test_get_missing_consume_times(dfbuyer_agent):
    missing_consumes = {"0x1": 10.5, "0x2": 20.3, "0x3": 30.7}
    prices = {"0x1": 2.5, "0x2": 3.3, "0x3": 4.7}
    result = dfbuyer_agent._get_missing_consume_times(missing_consumes, prices)
    expected_result = {"0x1": 5, "0x2": 7, "0x3": 7}
    assert result == expected_result


@patch("pdr_backend.dfbuyer.dfbuyer_agent.wait_until_subgraph_syncs")
@patch("time.sleep", return_value=None)
@patch.object(DFBuyerAgent, "_get_missing_consumes")
@patch.object(DFBuyerAgent, "_get_prices")
@patch.object(DFBuyerAgent, "_get_missing_consume_times")
@patch.object(DFBuyerAgent, "_batch_txs")
@patch.object(Web3Config, "get_block")
def test_take_step(
    mock_get_block,
    mock_batch_txs,
    mock_get_missing_consume_times,
    mock_get_prices,
    mock_get_missing_consumes,
    mock_sleep,
    mock_subgraph_sync,  # pylint: disable=unused-argument
    dfbuyer_agent,
):
    ts = 0
    mock_get_missing_consumes.return_value = {"0x1": 10.5, "0x2": 20.3, "0x3": 30.7}
    mock_get_prices.return_value = {"0x1": 2.5, "0x2": 3.3, "0x3": 4.7}
    mock_get_missing_consume_times.return_value = {"0x1": 5, "0x2": 7, "0x3": 7}
    mock_get_block.return_value = {"timestamp": 120}
    dfbuyer_agent.take_step(ts)
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


@patch.object(DFBuyerAgent, "take_step")
@patch.object(Web3Config, "get_block")
def test_run(mock_get_block, mock_take_step, dfbuyer_agent):
    mock_get_block.return_value = {"timestamp": 0}
    dfbuyer_agent.run(testing=True)
    mock_get_block.assert_called_once_with("latest")
    mock_take_step.assert_called_once_with(mock_get_block.return_value["timestamp"])


@patch("pdr_backend.dfbuyer.dfbuyer_agent.time.sleep", return_value=None)
def test_consume_method(mock_sleep, dfbuyer_agent):
    addresses_to_consume = ["0x1", "0x2"]
    times_to_consume = [2, 3]

    successful_tx = {"transactionHash": b"some_hash", "status": 1}
    failed_tx = {"transactionHash": b"some_hash", "status": 0}
    exception_tx = Exception("Error")

    with patch.object(
        dfbuyer_agent, "predictoor_batcher", autospec=True
    ) as mock_predictoor_batcher:
        mock_predictoor_batcher.consume_multiple.return_value = successful_tx
        assert dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

        mock_predictoor_batcher.consume_multiple.return_value = failed_tx
        assert not dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

        mock_predictoor_batcher.consume_multiple.side_effect = exception_tx
        with pytest.raises(Exception, match="Error"):
            dfbuyer_agent._consume(addresses_to_consume, times_to_consume)

        assert mock_sleep.call_count == dfbuyer_agent.config.max_request_tries


def test_consume_batch_method(dfbuyer_agent):
    addresses_to_consume = ["0x1", "0x2"]
    times_to_consume = [2, 3]

    with patch.object(
        dfbuyer_agent, "_consume", side_effect=[False, True, False, False, True]
    ) as mock_consume:
        dfbuyer_agent._consume_batch(addresses_to_consume, times_to_consume)
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
