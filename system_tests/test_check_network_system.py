import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.check_network.print_stats")
@patch("pdr_backend.analytics.check_network.check_dfbuyer")
def test_check_network(mock_print_stats, mock_check_dfbuyer):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.get_balance.return_value = 100
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.web3_config.owner = "0xowner"

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = int(5e18)
    mock_token.transfer.return_value = True

    mock_web3_pp.OCEAN_Token = mock_token
    mock_web3_pp.NativeToken = mock_token

    mock_query_subgraph = Mock()
    mock_query_subgraph.return_value = {
        "data": {
            "predictContracts": [
                {},
                {},
                {},
            ]
        }
    }
    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "sys.exit"
    ), patch("pdr_backend.analytics.check_network.query_subgraph", mock_query_subgraph):
        # Mock sys.argv
        sys.argv = ["pdr", "check_network", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        addresses = get_opf_addresses("sapphire-mainnet")
        # Verifying outputs
        mock_print.assert_any_call("pdr check_network: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("Number of Predictoor contracts: 3 - FAILED")
        mock_print.assert_any_call("Predictions:")
        mock_print.assert_any_call("True Values:")
        mock_print.assert_any_call("\nChecking account balances")

        for key in addresses.values():
            if key.startswith("pred"):
                mock_print.assert_any_call(
                    # pylint: disable=line-too-long
                    f"{key}: OCEAN: 5.00 WARNING LOW OCEAN BALANCE!, Native: 0.00 WARNING LOW NATIVE BALANCE!"
                )

        # Additional assertions
        mock_print_stats.assert_called()
        mock_check_dfbuyer.assert_called()
        mock_token.balanceOf.assert_called()
