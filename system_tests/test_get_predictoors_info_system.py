import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.get_predictoors_info.fetch_filtered_predictions")
@patch("pdr_backend.analytics.get_predictoors_info.get_cli_statistics")
@patch("pdr_backend.analytics.get_predictoors_info.save_prediction_csv")
def test_topup(
    mock_fetch_filtered_predictions, mock_get_cli_statistics, mock_save_prediction_csv
):
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
    with patch("pdr_backend.contract.token.Token", return_value=mock_token), patch(
        "pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp
    ):
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_predictoors_info",
            "2023-12-01",
            "2023-12-31",
            "./dir",
            "ppss.yaml",
            "development",
            "--PDRS",
            "0xpredictoor",
        ]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("dftool get_predictoors_info: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("PDRS=0xpredictoor")

        # Additional assertions
        mock_fetch_filtered_predictions.assert_called()
        mock_get_cli_statistics.assert_called()
        mock_save_prediction_csv.assert_called()
