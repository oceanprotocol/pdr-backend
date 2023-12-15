import time
from unittest.mock import Mock, patch

import pytest

from pdr_backend.util.check_network import (
    WEEK,
    check_dfbuyer,
    check_network_main,
    get_expected_consume,
    seconds_to_text,
)


def test_five_minutes():
    assert seconds_to_text(300) == "5m", "300 seconds should be converted to '5m'"


def test_one_hour():
    assert seconds_to_text(3600) == "1h", "3600 seconds should be converted to '1h'"


def test_zero_seconds():
    assert seconds_to_text(0) == "", "0 seconds should return an empty string"


def test_unhandled_seconds():
    assert seconds_to_text(100) == "", "Unhandled seconds should return an empty string"


def test_negative_seconds():
    assert seconds_to_text(-300) == "", "Negative seconds should return an empty string"


def test_non_integer_input():
    with pytest.raises(TypeError):
        seconds_to_text("300")


# pylint: disable=unused-argument
def mock_get_consume_so_far_per_contract(
    subgraph_url, dfbuyer_addr, ts_start_time, contract_addresses
):
    return {
        "0x1": 120,
    }


# pylint: disable=unused-argument
def mock_get_expected_consume(ts_now, tokens):
    return 100


@patch(
    "pdr_backend.util.check_network.get_consume_so_far_per_contract",
    side_effect=mock_get_consume_so_far_per_contract,
)
@patch(
    "pdr_backend.util.check_network.get_expected_consume",
    side_effect=mock_get_expected_consume,
)
def test_check_dfbuyer(
    mock_get_expected_consume_, mock_get_consume_so_far_per_contract_, capsys
):
    subgraph_url = "test_subgraph"
    dfbuyer_addr = "0x1"
    contract_query_result = {"data": {"predictContracts": [{"id": "0x1"}]}}
    tokens = []
    check_dfbuyer(dfbuyer_addr, contract_query_result, subgraph_url, tokens)
    captured = capsys.readouterr()

    assert (
        # pylint: disable=line-too-long
        "Checking consume amounts (dfbuyer), expecting 100 consume per contract\n    PASS... got 120 consume for contract: 0x1, expected 100\n"
        in captured.out
    )

    ts_now = time.time()
    ts_start_time = int((ts_now // WEEK) * WEEK)
    mock_get_consume_so_far_per_contract_.assert_called_once_with(
        subgraph_url, dfbuyer_addr, ts_start_time, ["0x1"]
    )
    mock_get_expected_consume_.assert_called_once_with(int(ts_now), tokens)


def test_get_expected_consume():
    # Test case 1: Beginning of the week
    for_ts = WEEK  # Start of the second week
    tokens = 140
    expected = tokens / 7 / 20  # Expected consumption for one interval
    assert get_expected_consume(for_ts, tokens) == expected

    # Test case 2: End of the first interval
    for_ts = WEEK + 86400  # Start of the second day of the second week
    expected = 2 * (tokens / 7 / 20)  # Expected consumption for two intervals
    assert get_expected_consume(for_ts, tokens) == expected

    # Test case 3: Middle of the week
    for_ts = WEEK + 3 * 86400  # Start of the fourth day of the second week
    expected = 4 * (tokens / 7 / 20)  # Expected consumption for four intervals
    assert get_expected_consume(for_ts, tokens) == expected

    # Test case 4: End of the week
    for_ts = 2 * WEEK - 1  # Just before the end of the second week
    expected = 7 * (tokens / 7 / 20)  # Expected consumption for seven intervals
    assert get_expected_consume(for_ts, tokens) == expected


@patch("pdr_backend.util.check_network.get_opf_addresses")
@patch("pdr_backend.util.subgraph.query_subgraph")
@patch("pdr_backend.util.check_network.Token")
def test_check_network_main(
    mock_token,
    mock_query_subgraph,
    mock_get_opf_addresses,
    _mock_ppss,
):
    mock_get_opf_addresses.return_value = {
        "dfbuyer": "0xdfBuyerAddress",
        "some_other_address": "0xSomeOtherAddress",
    }
    mock_query_subgraph.return_value = {"data": {"predictContracts": []}}
    mock_token.return_value.balanceOf.return_value = 1000 * 1e18

    mock_w3 = Mock()  # pylint: disable=not-callable
    mock_w3.eth.chain_id = 1
    mock_w3.eth.get_balance.return_value = 1000 * 1e18
    _mock_ppss.web3_pp.web3_config.w3 = mock_w3
    check_network_main(_mock_ppss, lookback_hours=24)

    mock_get_opf_addresses.assert_called_once_with(1)
    assert mock_query_subgraph.call_count == 1
    mock_token.assert_called()
    _mock_ppss.web3_pp.web3_config.w3.eth.get_balance.assert_called()
