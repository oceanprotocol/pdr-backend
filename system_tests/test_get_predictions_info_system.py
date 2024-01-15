import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.subgraph.subgraph_predictions import FilterMode
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.get_predictions_info.get_cli_statistics")
@patch("pdr_backend.analytics.get_predictions_info.fetch_filtered_predictions")
@patch("pdr_backend.analytics.get_predictions_info.save_analysis_csv")
@patch("pdr_backend.analytics.get_predictions_info.get_all_contract_ids_by_owner")
def test_topup(
    mock_get_all_contract_ids_by_owner,
    mock_save_analysis_csv,
    mock_fetch_filtered_predictions,
    mock_get_cli_statistics,
):
    mock_get_all_contract_ids_by_owner.return_value = ["0xfeed"]
    mock_predictions = [
        Prediction(
            "0xfeed",
            "BTC",
            "5m",
            True,
            100.0,
            False,
            100,
            "binance",
            10.0,
            10,
            "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152",
            "0xuser",
        )
    ]
    mock_fetch_filtered_predictions.return_value = mock_predictions

    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp):
        # Mock sys.argv
        sys.argv = [
            "pdr",
            "get_predictions_info",
            "2023-12-01",
            "2023-12-31",
            "./dir",
            "ppss.yaml",
            "development",
            "--FEEDS",
            "0xfeed",
        ]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("pdr get_predictions_info: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("FEEDS=0xfeed")

        # Additional assertions
        mock_save_analysis_csv.assert_called_with(mock_predictions, "./dir")
        mock_get_cli_statistics.assert_called_with(mock_predictions)
        mock_fetch_filtered_predictions.assert_called_with(
            1701388800,
            1703980800,
            ["0xfeed"],
            "mainnet",
            FilterMode.CONTRACT,
            payout_only=True,
            trueval_only=True,
        )
