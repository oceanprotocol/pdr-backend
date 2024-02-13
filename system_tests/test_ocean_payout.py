import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.predictoor_contract import PredictoorContract
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
    mock_web3_pp.web3_config = mock_web3_config

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = 100 * 1e18

    mock_query_pending_payouts = Mock()
    mock_query_pending_payouts.return_value = {"0x1": [1, 2, 3], "0x2": [5, 6, 7]}
    number_of_slots = 6  # 3 + 3

    mock_predictoor_contract = Mock(spec=PredictoorContract)
    mock_predictoor_contract.payout_multiple.return_value = None

    with patch(
        "pdr_backend.payout.payout.query_pending_payouts", mock_query_pending_payouts
    ), patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.contract.token.Token", return_value=mock_token
    ), patch(
        "pdr_backend.payout.payout.WrappedToken", return_value=mock_token
    ), patch(
        "pdr_backend.payout.payout.PredictoorContract",
        return_value=mock_predictoor_contract,
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "claim_OCEAN", "ppss.yaml"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        assert "pdr claim_OCEAN: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "Starting payout" in caplog.text
        assert "Finding pending payouts" in caplog.text
        assert f"Found {number_of_slots} slots" in caplog.text
        assert "Claiming payouts for 0x1" in caplog.text
        assert "Claiming payouts for 0x2" in caplog.text
        assert "Payout done" in caplog.text

        # Additional assertions
        mock_query_pending_payouts.assert_called_with(
            mock_web3_pp.subgraph_url, mock_web3_config.owner
        )
        mock_predictoor_contract.payout_multiple.assert_any_call([1, 2, 3], True)
        mock_predictoor_contract.payout_multiple.assert_any_call([5, 6, 7], True)
        assert mock_predictoor_contract.payout_multiple.call_count == 2
