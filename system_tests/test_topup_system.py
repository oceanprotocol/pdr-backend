import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.util.web3_config import Web3Config


def test_topup():
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.web3_config.owner = "0xowner"

    mock_token_rose = MagicMock(spec=NativeToken)
    balances_arr = [int(5000 * 1e18)] + [int(5 * 1e18)] * 100
    mock_token_rose.balanceOf.side_effect = balances_arr
    mock_token_rose.transfer.return_value = True
    mock_token_rose.name = "ROSE"

    mock_token = MagicMock(spec=Token)
    balances_arr = [int(5000 * 1e18)] + [int(5 * 1e18)] * 100
    mock_token.balanceOf.side_effect = balances_arr
    mock_token.transfer.return_value = True

    mock_web3_pp.OCEAN_Token = mock_token
    mock_web3_pp.NativeToken = mock_token

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "sys.exit"
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "topup", "ppss.yaml", "sapphire-testnet"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        addresses = get_opf_addresses("sapphire-mainnet")
        # Verifying outputs
        for key, value in addresses.items():
            mock_print.assert_any_call(f"{key}: 5.00 OCEAN, 5.00 ROSE")
            if key.startswith("pred"):
                mock_print.assert_any_call(f"\t Transferring 20 OCEAN to {value}...")
                mock_print.assert_any_call(f"\t Transferring 30 ROSE to {value}...")
            if key.startswith("dfbuyer"):
                mock_print.assert_any_call(f"\t Transferring 250 ROSE to {value}...")

        # Additional assertions
        mock_token.transfer.assert_called()
        mock_token.balanceOf.assert_called()
