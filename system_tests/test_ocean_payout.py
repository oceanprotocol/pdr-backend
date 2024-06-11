import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.payout.payout.wait_until_subgraph_syncs")
def test_ocean_payout_test(mock_wait_until_subgraph_syncs, caplog):
    _ = mock_wait_until_subgraph_syncs
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.owner = "0x00000000000000000000000000000000000c0ffe"
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.chain_id = SAPPHIRE_MAINNET_CHAINID

    def checksum_mock(_, y):
        return y

    mock_web3_config.w3.to_checksum_address = lambda x: x
    mock_web3_pp.web3_config = mock_web3_config

    mock_contract = Mock()
    mock_contract.get_payout = Mock()
    mock_contract.get_payout.return_value = {"transactionHash": b"0x1", "status": 1}
    mock_contract.pred_submitter_up_address.return_value = "0x1"
    mock_contract.pred_submitter_down_address.return_value = "0x1"

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = 100 * 1e18

    mock_query_pending_payouts = Mock()
    mock_query_pending_payouts.return_value = {"0x1": [1, 2, 3], "0x2": [5, 6, 7]}
    number_of_slots = 6  # 6 slots

    with patch(
        "pdr_backend.payout.payout.query_pending_payouts", mock_query_pending_payouts
    ), patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.contract.token.Token", return_value=mock_token
    ), patch(
        "pdr_backend.payout.payout.to_checksum", checksum_mock
    ), patch(
        "pdr_backend.payout.payout.WrappedToken", return_value=mock_token
    ), patch(
        "pdr_backend.payout.payout.PredSubmitterMgr", return_value=mock_contract
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "claim_OCEAN", "ppss.yaml"]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr claim_OCEAN: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "Starting payout" in caplog.text
        assert "Finding pending payouts" in caplog.text
        assert f"Found {number_of_slots} slots" in caplog.text
        assert "Payout tx 1/2: 307831" in caplog.text
        assert "Payout tx 1/2: 307831" in caplog.text
        assert "Payout done" in caplog.text

        # Additional assertions
        mock_query_pending_payouts.assert_called_with(mock_web3_pp.subgraph_url, "0x1")
        print(mock_contract.get_payout.call_args_list)
        mock_contract.get_payout.assert_any_call([1, 2, 3], ["0x1"])
        mock_contract.get_payout.assert_any_call([5, 6, 7], ["0x2"])
        assert mock_contract.get_payout.call_count == 2
