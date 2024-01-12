import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.dfbuyer.dfbuyer_agent.wait_until_subgraph_syncs")
@patch("pdr_backend.dfbuyer.dfbuyer_agent.time.sleep")
def test_dfbuyer_agent(mock_wait_until_subgraph_syncs, mock_time_sleep):
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

    mock_token = MagicMock()
    mock_token.balanceOf.return_value = 100 * 1e18
    mock_token.allowance.return_value = 1e128

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.get_block.return_value = {"timestamp": 100}
    mock_web3_config.owner = "0x00000000000000000000000000000000000c0ffe"
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.block_number = 100
    mock_web3_config.w3.eth.chain_id = SAPPHIRE_MAINNET_CHAINID
    mock_web3_config.w3.to_checksum_address.return_value = "0x1"

    mock_web3_pp.web3_config = mock_web3_config

    mock_get_consume_so_far_per_contract = Mock()
    mock_get_consume_so_far_per_contract.return_value = {"0x1": 120}

    mock_predictoor_batcher = Mock(spec=PredictoorBatcher)
    mock_predictoor_batcher.contract_address = "0xpredictoor_batcher"
    mock_predictoor_batcher.consume_multiple.return_value = {
        "transactionHash": b"0xbatch_submit_tx",
        "status": 1,
    }

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.cli.cli_module.get_address", return_value="0x1"
    ), patch("pdr_backend.dfbuyer.dfbuyer_agent.Token", return_value=mock_token), patch(
        "pdr_backend.dfbuyer.dfbuyer_agent.PredictoorBatcher",
        return_value=mock_predictoor_batcher,
    ), patch(
        "pdr_backend.dfbuyer.dfbuyer_agent.get_address", return_value="0x1"
    ), patch(
        "pdr_backend.dfbuyer.dfbuyer_agent.get_consume_so_far_per_contract",
        mock_get_consume_so_far_per_contract,
    ), patch(
        "pdr_backend.dfbuyer.dfbuyer_agent.DFBuyerAgent._get_prices",
        return_value={"0x1": 100},
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "dfbuyer", "ppss.yaml", "development"]

        with patch("builtins.print") as mock_print:
            cli_module._do_main()

        # Verifying outputs
        mock_print.assert_any_call("pdr dfbuyer: Begin")
        mock_print.assert_any_call("Arguments:")
        mock_print.assert_any_call("PPSS_FILE=ppss.yaml")
        mock_print.assert_any_call("NETWORK=development")
        mock_print.assert_any_call("  Feed: 5m binance BTC/USDT 0x1")
        mock_print.assert_any_call("Checking allowance...")
        mock_print.assert_any_call("Taking step for timestamp:", 100)
        mock_print.assert_any_call(
            "Missing consume amounts:", {"0x1": 5165.714285714285}
        )
        mock_print.assert_any_call("Missing consume times:", {"0x1": 52})
        mock_print.assert_any_call("Processing 3 batches...")
        mock_print.assert_any_call("Consuming contracts ['0x1'] for [20] times.")

        # Additional assertions
        mock_web3_pp.query_feed_contracts.assert_called()
        mock_predictoor_batcher.consume_multiple.assert_called()
        mock_time_sleep.assert_called()
        mock_get_consume_so_far_per_contract.assert_called()
