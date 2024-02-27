import sys
from unittest.mock import patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.currency_types import Wei, Eth


def test_rose_payout_test(caplog):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.web3_config.w3.eth.chain_id = SAPPHIRE_MAINNET_CHAINID

    mock_dfrewards = MagicMock()
    mock_dfrewards.get_claimable_rewards.return_value = Eth(100)
    mock_dfrewards.claim_rewards.return_value = None

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = Wei(100 * 1e18)

    with patch(
        "pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp
    ) as MockPPSS, patch(
        "pdr_backend.payout.payout.DFRewards", return_value=mock_dfrewards
    ), patch(
        "pdr_backend.contract.token.Token", return_value=mock_token
    ), patch(
        "pdr_backend.payout.payout.WrappedToken", return_value=mock_token
    ):
        mock_ppss_instance = MockPPSS.return_value
        mock_ppss_instance.web3_pp = mock_web3_pp

        # Mock sys.argv
        sys.argv = ["pdr", "claim_ROSE", "ppss.yaml"]

        cli_module._do_main()

        # Verifying outputs
        assert "Found 100 wROSE available to claim" in caplog.text
        assert "Claiming wROSE rewards..." in caplog.text
        assert "Converting wROSE to ROSE" in caplog.text
        assert "Found 100.0 wROSE, converting to ROSE..." in caplog.text
        assert "ROSE reward claim done" in caplog.text

        # Additional assertions
        mock_dfrewards.get_claimable_rewards.assert_called_with(
            mock_web3_pp.web3_config.owner,
            "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3",
        )
        mock_dfrewards.claim_rewards.assert_called_with(
            mock_web3_pp.web3_config.owner,
            "0x8Bc2B030b299964eEfb5e1e0b36991352E56D2D3",
        )
