from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_sync import (
    block_number_is_synced,
    wait_until_subgraph_syncs,
)
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_block_number_is_synced():
    def mock_response(url: str, query: str):  # pylint:disable=unused-argument
        if "number:50" in query:
            return {
                "errors": [
                    {
                        # pylint: disable=line-too-long
                        "message": "Failed to decode `block.number` value: `subgraph QmaGAi4jQw5L8J2xjnofAJb1PX5LLqRvGjsWbVehBELAUx only has data starting at block number 499 and data for block number 500 is therefore not available`"
                    }
                ]
            }

        return {"data": {"predictContracts": [{"id": "sample_id"}]}}

    with patch(
        "pdr_backend.subgraph.subgraph_sync.query_subgraph",
        side_effect=mock_response,
    ):
        assert block_number_is_synced("foo", 499) is True
        assert block_number_is_synced("foo", 500) is False
        assert block_number_is_synced("foo", 501) is False


@enforce_types
def test_wait_until_subgraph_syncs(capfd):
    mock_web3_config = Mock(spec=Web3Config)
    mock_web3_config.w3 = Mock()
    mock_web3_config.w3.eth = Mock()
    mock_web3_config.w3.eth.block_number = 500

    with patch(
        "pdr_backend.subgraph.subgraph_sync.block_number_is_synced",
        side_effect=[False, True],
    ):
        wait_until_subgraph_syncs(mock_web3_config, "foo")
