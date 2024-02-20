from typing import Dict
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_slot import (
    PredictSlot,
    fetch_slots,
    get_predict_slots_query,
    get_slots,
)


@enforce_types
def test_get_predict_slots_query():
    # Test the get_predict_slots_query function with expected inputs and outputs
    query = get_predict_slots_query(
        asset_ids=["0xAsset"], initial_slot=1000, last_slot=2000, first=10, skip=0
    )
    assert "predictSlots" in query
    assert "0xAsset" in query
    assert "1000" in query
    assert "2000" in query


# Sample data for tests
SAMPLE_PREDICT_QUERY_RESULT_ITEM = {
    "id": "0xAsset-12345",
    "slot": "12345",
    "trueValues": [{"ID": "1", "trueValue": True}],
    "roundSumStakesUp": 150.0,
    "roundSumStakes": 100.0,
}


MOCK_QUERY_RESPONSE = {"data": {"predictSlots": [SAMPLE_PREDICT_QUERY_RESULT_ITEM]}}

MOCK_QUERY_RESPONSE_FIRST_CALL = {
    "data": {
        "predictSlots": [SAMPLE_PREDICT_QUERY_RESULT_ITEM]
        * 1000  # Simulate a full page of results
    }
}

MOCK_QUERY_RESPONSE_SECOND_CALL: Dict[str, Dict[str, list]] = {
    "data": {"predictSlots": []}  # Simulate no further results, stopping the recursion
}


@enforce_types
@patch("pdr_backend.subgraph.subgraph_slot.query_subgraph")
def test_get_slots(mock_query_subgraph):
    # Configure the mock to return a full page of results on the first call,
    # and no results on the second call
    mock_query_subgraph.side_effect = [
        MOCK_QUERY_RESPONSE_FIRST_CALL,
        MOCK_QUERY_RESPONSE_SECOND_CALL,
    ]

    result_slots = get_slots(
        addresses=["0xAsset"],
        end_ts_param=2000,
        start_ts_param=1000,
        skip=0,
        slots=[],
        network="mainnet",
    )

    print("test_get_slots", result_slots)

    # Verify that the mock was called twice (once for the initial call, once for the recursive call)
    assert mock_query_subgraph.call_count == 2
    # Verify that the result contains the expected number of slots
    assert len(result_slots) == 1000
    # Verify that the slots contain instances of PredictSlot
    assert isinstance(result_slots[0], PredictSlot)
    # Verify the first slot's data matches the sample
    assert result_slots[0].ID == "0xAsset-12345"


@enforce_types
@patch(
    "pdr_backend.subgraph.subgraph_slot.query_subgraph",
    return_value=MOCK_QUERY_RESPONSE,
)
def test_fetch_slots_for_all_contracts(mock_query_subgraph):
    # Test logic for fetching slots for all contracts
    result = fetch_slots(
        contracts=["0xAsset"], start_ts_param=1000, end_ts_param=2000, network="mainnet"
    )

    print("test_fetch_slots_for_all_contracts", result)
    # Verify that the result is structured correctly
    assert "0xAsset" in result
    assert all(isinstance(slot, PredictSlot) for slot in result["0xAsset"])
    assert len(result["0xAsset"]) == 1
    assert result["0xAsset"][0].ID == "0xAsset-12345"
    # Verify that the mock was called
    mock_query_subgraph.assert_called()
