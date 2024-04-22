import sys
from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.web3_config import Web3Config


def setup_mock_web3_pp(mock_feeds, mock_feed_contract):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "development"
    mock_web3_pp.rpc_url = "http://example.com/rpc"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )
    mock_web3_pp.query_feed_contracts.return_value = mock_feeds
    mock_web3_pp.get_single_contract.return_value = mock_feed_contract
    mock_web3_pp.w3.eth.block_number = 100
    mock_predictoor_ss = Mock()
    mock_predictoor_ss.get_feed_from_candidates.return_value = mock_feeds["0x1"]
    mock_predictoor_ss.s_until_epoch_end = 100
    mock_predictoor_ss.s_start_payouts = 0

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.owner = "0xowner"
    mock_web3_config.get_block.return_value = {"timestamp": 100}
    mock_web3_pp.web3_config = mock_web3_config

    return mock_web3_pp, mock_predictoor_ss


def _test_predictoor_system(mock_feeds, mock_feed_contract, approach, caplog):
    mock_web3_pp, mock_predictoor_ss = setup_mock_web3_pp(
        mock_feeds, mock_feed_contract
    )
    mock_predictoor_ss.approach = approach

    merged_ohlcv_df = Mock()

    mock_predictoor_ss.get_feed_from_candidates.return_value = {
        "0x1": SubgraphFeed(
            "BTC/USDT", "0x1", "BTC", 300, 300, "0x1", "BTC", "5m", "binance"
        )
    }

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.ppss.ppss.PredictoorSS", return_value=mock_predictoor_ss
    ), patch(
        "pdr_backend.predictoor.predictoor_agent.PredSubmitterMgr", return_value=Mock()
    ), patch(
        "pdr_backend.lake.ohlcv_data_factory.OhlcvDataFactory.get_mergedohlcv_df",
        return_value=merged_ohlcv_df,
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "predictoor", "ppss.yaml", "development"]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr predictoor: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert f"APPROACH={approach}" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "Feed: 5m binance BTC/USDT 0x1" in caplog.text
        assert "Starting main loop." in caplog.text
        assert "Waiting..." in caplog.text

        # Additional assertions
        mock_predictoor_ss.get_feed_from_candidates.assert_called_once()
        mock_feed_contract.get_current_epoch.assert_called()


@patch("pdr_backend.ppss.ppss.PPSS.verify_feed_dependencies")
def test_predictoor_approach_1_system(
    mock_verify_feed_dependencies,
    mock_feeds,
    mock_feed_contract,
    caplog,
):
    _ = mock_verify_feed_dependencies
    _test_predictoor_system(mock_feeds, mock_feed_contract, 2, caplog)


@patch("pdr_backend.ppss.ppss.PPSS.verify_feed_dependencies")
def test_predictoor_approach_2_system(
    mock_verify_feed_dependencies,
    mock_feeds,
    mock_feed_contract,
    caplog,
):
    _ = mock_verify_feed_dependencies
    _test_predictoor_system(mock_feeds, mock_feed_contract, 2, caplog)
