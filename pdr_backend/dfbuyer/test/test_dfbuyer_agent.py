from unittest.mock import MagicMock, call, patch

from ccxt.base.exchange import math
from pdr_backend.dfbuyer.dfbuyer_agent import WEEK, DFBuyerAgent
from pdr_backend.util.constants import MAX_UINT, ZERO_ADDRESS


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
    n_intervals = int(time_passed / dfbuyer_agent.config.consume_interval_seconds)
    assert n_intervals == 3119
    expected_result = n_intervals * amount_per_feed_per_interval
    result = dfbuyer_agent._get_expected_amount_per_feed(ts)
    assert result == expected_result


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
    consume_times = {
        address: times for address, times in zip(addresses, [5, 15, 7, 3, 12, 8])
    }
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
