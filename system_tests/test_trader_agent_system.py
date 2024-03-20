import sys
from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.web3_config import Web3Config


def setup_mock_objects(mock_web3_pp, mock_feed_contract, feeds):
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )
    mock_web3_pp.query_feed_contracts.return_value = feeds

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.get_block.return_value = {"timestamp": 100}
    mock_web3_config.owner = "0x00000000000000000000000000000000000c0ffe"
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.block_number = 100
    mock_web3_config.w3.eth.chain_id = SAPPHIRE_MAINNET_CHAINID
    mock_web3_pp.web3_config = mock_web3_config

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = 100 * 1e18

    mock_trader_ss = Mock()
    mock_trader_ss.min_buffer = 1
    mock_trader_ss.get_feed_from_candidates.return_value = feeds["0x1"]

    mock_web3_pp.get_contracts.return_value = {"0x1": mock_feed_contract}

    return mock_web3_pp, mock_token, mock_trader_ss


def _test_trader(
    mock_time_sleep, mock_run, mock_feed_contract, mock_feeds, approach, caplog
):
    mock_web3_pp = MagicMock(spec=Web3PP)

    mock_web3_pp, mock_token, mock_trader_ss = setup_mock_objects(
        mock_web3_pp, mock_feed_contract, mock_feeds
    )

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.contract.token.Token", return_value=mock_token
    ), patch("pdr_backend.payout.payout.WrappedToken", return_value=mock_token), patch(
        "pdr_backend.payout.payout.FeedContract",
        return_value=mock_feed_contract,
    ), patch(
        "pdr_backend.ppss.ppss.TraderSS",
        return_value=mock_trader_ss,
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "trader", str(approach), "ppss.yaml", "development"]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr trader: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert f"APPROACH={approach}" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "Feed: 5m binance BTC/USDT 0x1" in caplog.text

        # Additional assertions
        mock_web3_pp.query_feed_contracts.assert_called()
        mock_trader_ss.get_feed_from_candidates.assert_called_with(mock_feeds)
        mock_time_sleep.assert_called()
        mock_run.assert_called()


@patch("pdr_backend.trader.base_trader_agent.BaseTraderAgent.run")
@patch("pdr_backend.trader.base_trader_agent.time.sleep")
def test_trader_approach_1(
    mock_time_sleep, mock_run, mock_feed_contract, mock_feeds, caplog
):
    _test_trader(mock_time_sleep, mock_run, mock_feed_contract, mock_feeds, 1, caplog)


@patch("pdr_backend.trader.base_trader_agent.BaseTraderAgent.run")
@patch("pdr_backend.trader.base_trader_agent.time.sleep")
def test_trader_approach_2(
    mock_time_sleep, mock_run, mock_feed_contract, mock_feeds, caplog
):
    _test_trader(mock_time_sleep, mock_run, mock_feed_contract, mock_feeds, 2, caplog)
