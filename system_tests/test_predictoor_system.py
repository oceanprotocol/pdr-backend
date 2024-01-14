import sys
from unittest.mock import Mock, patch, MagicMock
from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config


def setup_mock_web3_pp(mock_feeds, mock_predictoor_contract):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "development"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )
    mock_web3_pp.query_feed_contracts.return_value = mock_feeds
    mock_web3_pp.get_contracts.return_value = {"0x1": mock_predictoor_contract}
    mock_web3_pp.w3.eth.block_number = 100
    mock_predictoor_ss = Mock()
    mock_predictoor_ss.get_feed_from_candidates.return_value = mock_feeds["0x1"]
    mock_predictoor_ss.s_until_epoch_end = 100

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.get_block.return_value = {"timestamp": 100}
    mock_web3_pp.web3_config = mock_web3_config

    return mock_web3_pp, mock_predictoor_ss


def test_predictoor_approach_1_system(mock_feeds, mock_predictoor_contract):
    mock_web3_pp, mock_predictoor_ss = setup_mock_web3_pp(
        mock_feeds, mock_predictoor_contract
    )

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.publisher.publish_assets.get_address", return_value="0x1"
    ), patch("pdr_backend.ppss.ppss.PredictoorSS", return_value=mock_predictoor_ss):
        # Mock sys.argv
        sys.argv = ["pdr", "predictoor", "1", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("pdr predictoor: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("APPROACH=1")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("  Feed: 5m binance BTC/USDT 0x1")
        mock_print.assert_any_call("Starting main loop.")
        mock_print.assert_any_call("Waiting...", end="")

        # Additional assertions
        mock_predictoor_ss.get_feed_from_candidates.assert_called_once()
        mock_predictoor_contract.get_current_epoch.assert_called()


def test_predictoor_approach_3_system(mock_feeds, mock_predictoor_contract):
    mock_web3_pp, mock_predictoor_ss = setup_mock_web3_pp(
        mock_feeds, mock_predictoor_contract
    )

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.publisher.publish_assets.get_address", return_value="0x1"
    ), patch("pdr_backend.ppss.ppss.PredictoorSS", return_value=mock_predictoor_ss):
        # Mock sys.argv
        sys.argv = ["pdr", "predictoor", "3", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("pdr predictoor: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("APPROACH=3")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("  Feed: 5m binance BTC/USDT 0x1")
        mock_print.assert_any_call("Starting main loop.")
        mock_print.assert_any_call("Waiting...", end="")

        # Additional assertions
        mock_predictoor_ss.get_feed_from_candidates.assert_called_once()
        mock_predictoor_contract.get_current_epoch.assert_called()
