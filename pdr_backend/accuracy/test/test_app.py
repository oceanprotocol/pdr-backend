from typing import List
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import ContractIdAndSPE
from pdr_backend.accuracy.app import (
    calculate_prediction_result,
    process_single_slot,
    aggregate_statistics,
    calculate_statistics_for_all_assets,
)
from pdr_backend.subgraph.subgraph_slot import PredictSlot
from pdr_backend.util.time_types import UnixTimeS

# Sample data for tests
SAMPLE_PREDICT_SLOT = PredictSlot(
    ID="0xAsset-12345",
    slot="12345",
    trueValues=[{"ID": "1", "trueValue": True}],
    roundSumStakesUp=150.0,
    roundSumStakes=100.0,
)


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
        slot=SAMPLE_PREDICT_SLOT, end_of_previous_day_timestamp=UnixTimeS(12340)
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
        slots=[SAMPLE_PREDICT_SLOT],
        end_of_previous_day_timestamp=UnixTimeS(12340),
    )
    assert total_staked_yesterday == 0.0
    assert total_staked_today == 100.0
    assert total_correct_predictions == 1
    assert total_slots_evaluated == 1


@enforce_types
@patch("pdr_backend.accuracy.app.fetch_slots_for_all_assets")
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
        start_ts_param=UnixTimeS(91000),
        end_ts_param=UnixTimeS(92000),
        network="mainnet",
    )

    print("test_calculate_statistics_for_all_assets", statistics)
    # Verify
    assert statistics["0xAsset"]["average_accuracy"] == 100.0
    mock_fetch_slots.assert_called_once_with(
        ["0xAsset"], UnixTimeS(91000), UnixTimeS(92000), "mainnet"
    )
