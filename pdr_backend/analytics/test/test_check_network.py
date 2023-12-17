from unittest.mock import Mock, patch

from enforce_typing import enforce_types

from pdr_backend.util.constants import S_PER_DAY, S_PER_WEEK
from pdr_backend.analytics.check_network import (
    check_dfbuyer,
    check_network_main,
    get_expected_consume,
    _N_FEEDS,
)
from pdr_backend.ppss.ppss import mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override
from pdr_backend.util.mathutil import to_wei


PATH = "pdr_backend.analytics.check_network"

MOCK_CUR_UT = 1702826080982


@enforce_types
@patch(
    f"{PATH}.get_consume_so_far_per_contract",
    side_effect=Mock(return_value={"0x1": 120}),
)
@patch(
    f"{PATH}.get_expected_consume",
    side_effect=Mock(return_value=100),
)
@patch(
    f"{PATH}.current_ut",
    side_effect=Mock(return_value=MOCK_CUR_UT),
)
def test_check_dfbuyer(  # pylint: disable=unused-argument
    mock_current_ut,
    mock_get_expected_consume_,
    mock_get_consume_so_far_per_contract_,
    capsys,
):
    dfbuyer_addr = "0x1"
    contract_query_result = {"data": {"predictContracts": [{"id": "0x1"}]}}
    subgraph_url = "test_dfbuyer"
    token_amt = 3
    check_dfbuyer(dfbuyer_addr, contract_query_result, subgraph_url, token_amt)
    captured = capsys.readouterr()

    target_str = (
        "Checking consume amounts (dfbuyer), "
        "expecting 100 consume per contract\n    "
        "PASS... got 120 consume for contract: 0x1, expected 100\n"
    )
    assert target_str in captured.out

    cur_ut = MOCK_CUR_UT
    start_ut = int((cur_ut // S_PER_WEEK) * S_PER_WEEK)
    mock_get_consume_so_far_per_contract_.assert_called_once_with(
        subgraph_url, dfbuyer_addr, start_ut, ["0x1"]
    )
    mock_get_expected_consume_.assert_called_once_with(int(cur_ut), token_amt)


@enforce_types
def test_get_expected_consume():
    # Test case 1: Beginning of week
    for_ut = S_PER_WEEK  # Start of second week
    token_amt = 140
    expected = token_amt / 7 / _N_FEEDS  # Expected consume for one interval
    assert get_expected_consume(for_ut, token_amt) == expected

    # Test case 2: End of first interval
    for_ut = S_PER_WEEK + S_PER_DAY  # Start of second day of second week
    expected = 2 * (token_amt / 7 / _N_FEEDS)  # Expected consume for two intervals
    assert get_expected_consume(for_ut, token_amt) == expected

    # Test case 3: Middle of week
    for_ut = S_PER_WEEK + 3 * S_PER_DAY  # Start of fourth day of second week
    expected = 4 * (token_amt / 7 / _N_FEEDS)  # Expected consume for four intervals
    assert get_expected_consume(for_ut, token_amt) == expected

    # Test case 4: End of week
    for_ut = 2 * S_PER_WEEK - 1  # Just before end of second week
    expected = 7 * (token_amt / 7 / _N_FEEDS)  # Expected consume for seven intervals
    assert get_expected_consume(for_ut, token_amt) == expected


@enforce_types
@patch(f"{PATH}.get_opf_addresses")
@patch(f"{PATH}.query_subgraph")
@patch(f"{PATH}.Token")
def test_check_network_main(
    mock_token,
    mock_query_subgraph,
    mock_get_opf_addresses,
    tmpdir,
    monkeypatch,
):
    del_network_override(monkeypatch)
    ppss = mock_ppss("5m", ["binance c BTC/USDT"], "sapphire-mainnet", str(tmpdir))
    mock_get_opf_addresses.return_value = {
        "dfbuyer": "0xdfBuyerAddress",
        "some_other_address": "0xSomeOtherAddress",
    }
    mock_query_subgraph.return_value = {"data": {"predictContracts": []}}
    mock_token.return_value.balanceOf.return_value = to_wei(1000)

    mock_w3 = Mock()  # pylint: disable=not-callable
    mock_w3.eth.chain_id = 1
    mock_w3.eth.get_balance.return_value = to_wei(1000)
    ppss.web3_pp.web3_config.w3 = mock_w3
    check_network_main(ppss, lookback_hours=24)

    mock_get_opf_addresses.assert_called_once_with("sapphire-mainnet")
    assert mock_query_subgraph.call_count == 1
    mock_token.assert_called()
    ppss.web3_pp.web3_config.w3.eth.get_balance.assert_called()
