from unittest.mock import Mock, call, patch

import pytest

from pdr_backend.models.dfrewards import DFRewards
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.predictoor.payout import (
    batchify,
    do_payout,
    do_rose_payout,
    request_payout_batches,
)
from pdr_backend.util.web3_config import Web3Config


def test_batchify():
    assert batchify([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert batchify([], 2) == []
    assert batchify([1, 2], 5) == [[1, 2]]
    assert batchify([1, 2, 3, 4, 5, 6, 7], 3) == [[1, 2, 3], [4, 5, 6], [7]]
    with pytest.raises(Exception):
        batchify("12345", 2)


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


def test_do_payout():
    mock_config = Mock()
    mock_config.subgraph_url = ""
    mock_config.web3_config = Mock(spec=Web3Config)
    mock_config.web3_config.owner = "mock_owner"

    mock_batch_size = "5"

    mock_pending_payouts = {
        "address_1": [1, 2, 3],
        "address_2": [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    }

    mock_contract = Mock(spec=PredictoorContract)
    mock_contract.payout_multiple = Mock()

    with patch(
        "pdr_backend.predictoor.payout.BaseConfig", return_value=mock_config
    ), patch("pdr_backend.predictoor.payout.wait_until_subgraph_syncs"), patch(
        "os.getenv", return_value=mock_batch_size
    ), patch(
        "pdr_backend.predictoor.payout.query_pending_payouts",
        return_value=mock_pending_payouts,
    ), patch(
        "pdr_backend.predictoor.payout.PredictoorContract", return_value=mock_contract
    ):
        do_payout()
        print(mock_contract.payout_multiple.call_args_list)
        call_args = mock_contract.payout_multiple.call_args_list
        assert call_args[0] == call([1, 2, 3], True)
        assert call_args[1] == call([4, 5, 6, 7, 8], True)
        assert call_args[2] == call([9, 10, 11, 12, 13], True)
        assert call_args[3] == call([14, 15], True)
        assert len(call_args) == 4


def test_do_rose_payout():
    mock_config = Mock()
    mock_config.subgraph_url = ""
    mock_config.web3_config = Mock(spec=Web3Config)
    mock_config.web3_config.eth = Mock()
    mock_config.web3_config.eth.chain_id = 23294
    mock_config.web3_config.owner = "mock_owner"

    mock_contract = Mock(spec=DFRewards)
    mock_contract.get_claimable_rewards = Mock()
    mock_contract.get_claimable_rewards.return_value = 100
    mock_contract.claim_rewards = Mock()

    with patch(
        "pdr_backend.predictoor.payout.BaseConfig", return_value=mock_config
    ), patch("pdr_backend.predictoor.payout.DFRewards", return_value=mock_contract):
        do_rose_payout()
        mock_contract.claim_rewards.assert_called_with(
            "mock_owner", "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3"
        )
