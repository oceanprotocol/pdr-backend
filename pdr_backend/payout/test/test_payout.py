from unittest.mock import Mock, call, patch

import pytest
from enforce_typing import enforce_types

from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.contract.wrapped_token import WrappedToken
from pdr_backend.payout.payout import (
    batchify,
    do_ocean_payout,
    do_rose_payout,
    request_payout_batches,
)
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str


@enforce_types
def test_batchify():
    assert batchify([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert batchify([], 2) == []
    assert batchify([1, 2], 5) == [[1, 2]]
    assert batchify([1, 2, 3, 4, 5, 6, 7], 3) == [[1, 2, 3], [4, 5, 6], [7]]
    with pytest.raises(Exception):
        batchify("12345", 2)


@enforce_types
def test_request_payout_batches():
    mock_contract = Mock(spec=PredictoorContract)
    mock_contract.payout_multiple = Mock()

    timestamps = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    batch_size = 3

    request_payout_batches(mock_contract, batch_size, timestamps)

    mock_contract.payout_multiple.assert_has_calls(
        [
            call([1, 2, 3], True),
            call([4, 5, 6], True),
            call([7, 8, 9], True),
        ]
    )

    assert mock_contract.payout_multiple.call_count == 3


@enforce_types
def test_do_ocean_payout(tmpdir):
    ppss = _ppss(tmpdir)
    ppss.payout_ss.set_batch_size(5)

    mock_pending_payouts = {
        "address_1": [1, 2, 3],
        "address_2": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    }

    mock_contract = Mock(spec=PredictoorContract)
    mock_contract.payout_multiple = Mock()

    with patch("pdr_backend.payout.payout.wait_until_subgraph_syncs"), patch(
        "pdr_backend.payout.payout.query_pending_payouts",
        return_value=mock_pending_payouts,
    ), patch(
        "pdr_backend.payout.payout.PredictoorContract", return_value=mock_contract
    ):
        do_ocean_payout(ppss, check_network=False)
        print(mock_contract.payout_multiple.call_args_list)
        call_args = mock_contract.payout_multiple.call_args_list
        assert call_args[0] == call([1, 2, 3], True)
        assert call_args[1] == call([4, 5, 6, 7, 8], True)
        assert call_args[2] == call([9, 10, 11, 12, 13], True)
        assert call_args[3] == call([14, 15], True)
        assert len(call_args) == 4


@enforce_types
def test_do_rose_payout(tmpdir):
    ppss = _ppss(tmpdir)
    web3_config = ppss.web3_pp.web3_config

    mock_contract = Mock(spec=DFRewards)
    mock_contract.get_claimable_rewards = Mock()
    mock_contract.get_claimable_rewards.return_value = 100
    mock_contract.claim_rewards = Mock()

    mock_wrose = Mock(spec=WrappedToken)
    mock_wrose.balanceOf = Mock()
    mock_wrose.balanceOf.return_value = 100
    mock_wrose.withdraw = Mock()

    with patch("pdr_backend.payout.payout.time"), patch(
        "pdr_backend.payout.payout.WrappedToken", return_value=mock_wrose
    ), patch("pdr_backend.payout.payout.DFRewards", return_value=mock_contract):
        do_rose_payout(ppss, check_network=False)
        mock_contract.claim_rewards.assert_called_with(
            web3_config.owner, "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"
        )
        mock_wrose.balanceOf.assert_called()
        mock_wrose.withdraw.assert_called_with(100)


@enforce_types
def _ppss(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="sapphire-mainnet")
    return ppss
