import sys

from unittest.mock import Mock, patch, MagicMock
from pdr_backend.lake.table_pdr_predictions import (
    _object_list_to_df,
    predictions_schema,
)
from pdr_backend.subgraph.prediction import Prediction
from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.analytics.get_predictions_info.get_feed_summary_stats")
@patch("pdr_backend.analytics.get_predictions_info.GQLDataFactory.get_gql_dfs")
def test_topup(mock_get_polars, mock_get_stats):
    feed_addr = "0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152"
    user_addr = "0xaaaa4cb4ff2584bad80ff5f109034a891c3d88dd"
    mock_predictions = [
        Prediction(
            "{feed_addr}-31232-{user_addr}",
            "BTC",
            "5m",
            True,
            100.0,
            False,
            1701532572,
            "binance",
            10.0,
            10,
            feed_addr,
            user_addr,
        )
    ]
    predictions_df = _object_list_to_df(mock_predictions, predictions_schema)

    mock_get_stats.return_value = predictions_df
    mock_get_polars.return_value = {"pdr_predictions": predictions_df}

    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config
    mock_web3_pp.owner_addrs = user_addr

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
            "{feed_addr}",
        ]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("pdr get_predictions_info: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("FEEDS={feed_addr}")

        # Additional assertions
        mock_get_polars.assert_called_with()
        mock_get_stats.call_args[0][0].equals(predictions_df)
