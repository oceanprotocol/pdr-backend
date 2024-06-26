#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.contract.slot import Slot
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.constants import SAPPHIRE_MAINNET_CHAINID
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.trueval.trueval_agent.wait_until_subgraph_syncs")
@patch("pdr_backend.trueval.trueval_agent.time.sleep")
@patch("pdr_backend.trueval.trueval_agent.TruevalAgent.process_trueval_slot")
def test_trueval_batch(
    mock_wait_until_subgraph_syncs, mock_time_sleep, mock_process, caplog
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
    mock_web3_pp.get_pending_slots.return_value = [Slot(1, feeds["0x1"])]
    mock_web3_pp.get_address.return_value = "0x1"

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.get_block.return_value = {"timestamp": 100}
    mock_web3_config.owner = "0x00000000000000000000000000000000000c0ffe"
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth.block_number = 100
    mock_web3_config.w3.eth.chain_id = SAPPHIRE_MAINNET_CHAINID
    mock_web3_pp.web3_config = mock_web3_config

    mock_predictoor_batcher = Mock(spec=PredictoorBatcher)

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp), patch(
        "pdr_backend.trueval.trueval_agent.PredictoorBatcher",
        return_value=mock_predictoor_batcher,
    ), patch(
        "pdr_backend.trueval.trueval_agent.TruevalAgent.process_trueval_slot"
    ), patch(
        "pdr_backend.trueval.trueval_agent.TruevalAgent.batch_submit_truevals",
        return_value="0xbatch_submit_tx",
    ):
        # Mock sys.argv
        sys.argv = ["pdr", "trueval", "ppss.yaml", "development"]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr trueval: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "Found 1 pending slots, processing 30" in caplog.text
        assert "Tx sent: 0xbatch_submit_tx, sleeping for 30 seconds..." in caplog.text

        # Additional assertions
        mock_web3_pp.get_pending_slots.assert_called()
        mock_time_sleep.assert_called()
        mock_process.assert_called()
