from unittest.mock import patch
from dataclasses import asdict
from typing import Dict
from enforce_typing import enforce_types

from pdr_backend.util.subgraph_slot import (
    get_predict_slots_query,
    get_slots,
    fetch_slots_for_all_assets,
    calculate_prediction_prediction_result,
    process_single_slot,
    aggregate_statistics,
    calculate_statistics_for_all_assets,
    PredictSlot,
)

# Sample data for tests
SAMPLE_PREDICT_SLOT = PredictSlot(
    id="1-12345",
    slot="12345",
    trueValues=[{"id": "1", "trueValue": True}],
    roundSumStakesUp=150.0,
    roundSumStakes=100.0,
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
SAMPLE_PREDICT_SLOT = PredictSlot(
    id="0xAsset-12345",
    slot="12345",
    trueValues=[{"id": "1", "trueValue": True}],
    roundSumStakesUp=150.0,
    roundSumStakes=100.0,
)


MOCK_QUERY_RESPONSE = {"data": {"predictSlots": [asdict(SAMPLE_PREDICT_SLOT)]}}

MOCK_QUERY_RESPONSE_FIRST_CALL = {
    "data": {
        "predictSlots": [asdict(SAMPLE_PREDICT_SLOT)]
        * 1000  # Simulate a full page of results
    }
}

MOCK_QUERY_RESPONSE_SECOND_CALL: Dict[str, Dict[str, list]] = {
    "data": {"predictSlots": []}  # Simulate no further results, stopping the recursion
}


@enforce_types
@patch("pdr_backend.util.subgraph_slot.query_subgraph")
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
    assert result_slots[0].id == "0xAsset-12345"


@enforce_types
def test_calculate_prediction_prediction_result():
    # Test the calculate_prediction_prediction_result function with expected inputs
    result = calculate_prediction_prediction_result(150.0, 100.0)
    assert result["direction"]

    result = calculate_prediction_prediction_result(100.0, 150.0)
    assert not result["direction"]


@enforce_types
def test_process_single_slot():
    # Test the process_single_slot function
    (
        staked_yesterday,
        staked_today,
        correct_predictions,
        slots_evaluated,
    ) = process_single_slot(
        slot=SAMPLE_PREDICT_SLOT, end_of_previous_day_timestamp=12340
    )

    assert staked_yesterday == 0.0
    assert staked_today == 100.0
    assert correct_predictions == 1
    assert slots_evaluated == 1


@enforce_types
def test_aggregate_statistics():
    # Test the aggregate_statistics function
    (
        total_staked_yesterday,
        total_staked_today,
        total_correct_predictions,
        total_slots_evaluated,
    ) = aggregate_statistics(
        slots=[SAMPLE_PREDICT_SLOT], end_of_previous_day_timestamp=12340
    )
    assert total_staked_yesterday == 0.0
    assert total_staked_today == 100.0
    assert total_correct_predictions == 1
    assert total_slots_evaluated == 1


@enforce_types
@patch("pdr_backend.util.subgraph_slot.fetch_slots_for_all_assets")
def test_calculate_statistics_for_all_assets(mock_fetch_slots):
    # Set up the mock to return a predetermined value
    mock_fetch_slots.return_value = {"0xAsset": [SAMPLE_PREDICT_SLOT] * 1000}
    # Test the calculate_statistics_for_all_assets function
    statistics = calculate_statistics_for_all_assets(
        asset_ids=["0xAsset"], start_ts_param=1000, end_ts_param=2000, network="mainnet"
    )
    # Verify that the statistics are calculated as expected
    assert statistics["0xAsset"]["average_accuracy"] == 100.0
    # Verify that the mock was called as expected
    mock_fetch_slots.assert_called_once_with(["0xAsset"], 1000, 2000, "mainnet")


@enforce_types
@patch(
    "pdr_backend.util.subgraph_slot.query_subgraph", return_value=MOCK_QUERY_RESPONSE
)
def test_fetch_slots_for_all_assets(mock_query_subgraph):
    # Test the fetch_slots_for_all_assets function
    result = fetch_slots_for_all_assets(
        asset_ids=["0xAsset"], start_ts_param=1000, end_ts_param=2000, network="mainnet"
    )

    print("test_fetch_slots_for_all_assets", result)
    # Verify that the result is structured correctly
    assert "0xAsset" in result
    assert all(isinstance(slot, PredictSlot) for slot in result["0xAsset"])
    assert len(result["0xAsset"]) == 1
    assert result["0xAsset"][0].id == "0xAsset-12345"
    # Verify that the mock was called
    mock_query_subgraph.assert_called()
