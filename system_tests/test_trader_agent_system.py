import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.payout.payout.wait_until_subgraph_syncs")
@patch("pdr_backend.trader.base_trader_agent.time.sleep")
@patch("pdr_backend.trader.base_trader_agent.BaseTraderAgent.run")
def test_trader_approach_1_and_2(
    mock_wait_until_subgraph_syncs, mock_time_sleep, mock_run
):
    _ = mock_wait_until_subgraph_syncs
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "sapphire-mainnet"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )
    feeds = {
        "0x1": SubgraphFeed(
            "Feed: binance | BTC/USDT | 5m",
            "0x1",
            "BTC",
            100,
            300,
            "0xf",
            "BTC/USDT",
            "5m",
            "binance",
        )
    }
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

    mock_predictoor_contract = Mock(spec=PredictoorContract)
    mock_predictoor_contract.payout_multiple.return_value = None
    mock_predictoor_contract.get_agg_predval.return_value = (12, 23)

    mock_trader_ss = Mock()
    mock_trader_ss.min_buffer = 1
    mock_trader_ss.get_feed_from_candidates.return_value = feeds["0x1"]

    mock_web3_pp.get_contracts.return_value = {"0x1": mock_predictoor_contract}

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.contract.token.Token", return_value=mock_token
    ), patch("pdr_backend.payout.payout.WrappedToken", return_value=mock_token), patch(
        "pdr_backend.payout.payout.PredictoorContract",
        return_value=mock_predictoor_contract,
    ), patch(
        "pdr_backend.ppss.ppss.TraderSS",
        return_value=mock_trader_ss,
    ):
        # Mock sys.argv approach 1
        sys.argv = ["pdr", "trader", "1", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

            # Verifying outputs
            mock_print.assert_any_call("dftool trader: Begin")
            mock_print.assert_any_call("Arguments:")
            mock_print.assert_any_call("APPROACH=1")
            mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
            mock_print.assert_any_call("NETWORK=development")
            mock_print.assert_any_call("  Feed: 5m binance BTC/USDT 0x1")

            # Additional assertions
            mock_web3_pp.query_feed_contracts.assert_called()
            mock_trader_ss.get_feed_from_candidates.assert_called_with(feeds)

        # Mock sys.argv approach 2
        sys.argv = ["pdr", "trader", "2", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

            # Verifying outputs
            mock_print.assert_any_call("dftool trader: Begin")
            mock_print.assert_any_call("Arguments:")
            mock_print.assert_any_call("APPROACH=2")
            mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
            mock_print.assert_any_call("NETWORK=development")
            mock_print.assert_any_call("  Feed: 5m binance BTC/USDT 0x1")

            # Additional assertions
            mock_web3_pp.query_feed_contracts.assert_called()
            mock_trader_ss.get_feed_from_candidates.assert_called_with(feeds)
