from dataclasses import asdict
from typing import Dict, List
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import ContractIdAndSPE
from pdr_backend.subgraph.subgraph_slot import (
    PredictSlot,
    aggregate_statistics,
    calculate_prediction_result,
    calculate_statistics_for_all_assets,
    fetch_slots_for_all_assets,
    get_predict_slots_query,
    get_slots,
    process_single_slot,
)

# Sample data for tests
SAMPLE_PREDICT_SLOT = PredictSlot(
    ID="1-12345",
    slot="12345",
    trueValues=[{"ID": "1", "trueValue": True}],
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
    ID="0xAsset-12345",
    slot="12345",
    trueValues=[{"ID": "1", "trueValue": True}],
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
def test_calculate_prediction_result():
    # Test the calculate_prediction_prediction_result function with expected inputs
    result = calculate_prediction_result(150.0, 200.0)
    assert result

    result = calculate_prediction_result(100.0, 250.0)
    assert not result


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
@patch("pdr_backend.subgraph.subgraph_slot.fetch_slots_for_all_assets")
def test_calculate_statistics_for_all_assets(mock_fetch_slots):
    # Mocks
    mock_fetch_slots.return_value = {"0xAsset": [SAMPLE_PREDICT_SLOT] * 1000}
    contracts_list: List[ContractIdAndSPE] = [
        {"ID": "0xAsset", "seconds_per_epoch": 300, "name": "TEST/USDT"}
    ]

    # Main work
    statistics = calculate_statistics_for_all_assets(
        asset_ids=["0xAsset"],
        contracts_list=contracts_list,
        start_ts_param=1000,
        end_ts_param=2000,
        network="mainnet",
    )

    # Verify
    assert statistics["0xAsset"]["average_accuracy"] == 100.0
    mock_fetch_slots.assert_called_once_with(["0xAsset"], 1000, 2000, "mainnet")


@enforce_types
@patch(
    "pdr_backend.subgraph.subgraph_slot.query_subgraph",
    return_value=MOCK_QUERY_RESPONSE,
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
    assert result["0xAsset"][0].ID == "0xAsset-12345"
    # Verify that the mock was called
    mock_query_subgraph.assert_called()
