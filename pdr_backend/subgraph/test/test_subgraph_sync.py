from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_sync import block_number_is_synced


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
