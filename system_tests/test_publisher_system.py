#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import sys

from unittest.mock import Mock, patch, MagicMock

from pdr_backend.cli import cli_module
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config


@patch("pdr_backend.cli.cli_module.fund_accounts_with_OCEAN")
@patch("pdr_backend.publisher.publish_assets.publish_asset")
def test_publisher(mock_fund_accounts, mock_publish_asset, caplog):
    mock_web3_pp = MagicMock(spec=Web3PP)
    mock_web3_pp.network = "development"
    mock_web3_pp.subgraph_url = (
        "http://localhost:8000/subgraphs/name/oceanprotocol/ocean-subgraph"
    )

    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_pp.web3_config = mock_web3_config

    with patch("pdr_backend.ppss.ppss.Web3PP", return_value=mock_web3_pp):
        # Mock sys.argv
        sys.argv = ["pdr", "publisher", "ppss.yaml", "development"]

        cli_module._do_main()

        # Verifying outputs
        assert "pdr publisher: Begin" in caplog.text
        assert "Arguments:" in caplog.text
        assert "PPSS_FILE=ppss.yaml" in caplog.text
        assert "NETWORK=development" in caplog.text
        assert "Publish on network = development" in caplog.text
        assert "Done publishing." in caplog.text

        # Additional assertions
        mock_fund_accounts.assert_called()
        mock_publish_asset.assert_called()
