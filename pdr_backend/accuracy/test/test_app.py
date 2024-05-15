from typing import List

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import ContractIdAndSPE
from pdr_backend.accuracy.app import (
    calculate_prediction_result,
    process_single_slot,
    aggregate_statistics,
    calculate_statistics_for_all_assets,
)
from pdr_backend.lake.slot import Slot
from pdr_backend.util.time_types import UnixTimeS

# Sample data for tests
SAMPLE_PREDICT_SLOT = Slot(
    ID="0xAsset-12345",
    timestamp=12345,
    slot=12345,
    truevalue=True,
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
def test_calculate_statistics_for_all_assets():
    # Mocks
    all_slots = [SAMPLE_PREDICT_SLOT] * 1000
    contracts_list: List[ContractIdAndSPE] = [
        {"ID": "0xAsset", "seconds_per_epoch": 300, "name": "TEST/USDT"}
    ]

    # Main work
    statistics = calculate_statistics_for_all_assets(
        contracts_list=contracts_list,
        all_slots=all_slots,
        end_ts_param=UnixTimeS(92000),
    )

    print("test_calculate_statistics_for_all_assets", statistics)
    # Verify
    assert statistics["0xAsset"]["average_accuracy"] == 100.0
