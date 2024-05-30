from typing import List
from datetime import datetime, timedelta
from unittest.mock import patch

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import ContractIdAndSPE
from pdr_backend.accuracy.app import (
    calculate_prediction_result,
    process_single_slot,
    aggregate_statistics,
    calculate_statistics_for_all_assets,
    calculate_statistics_from_slots,
)
from pdr_backend.lake.slot import Slot
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.ppss.ppss import mock_ppss

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


@enforce_types
def test_calculate_statistics_from_DuckDB_tables(tmpdir):
    ppss = mock_ppss(
        [{"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 5m"}],
        "sapphire-mainnet",
        str(tmpdir),
        st_timestr="2023-12-20",
        fin_timestr="now",
    )

    two_weeks_ago = datetime.utcnow() - timedelta(weeks=2)
    slot_timestamp = UnixTimeS(int(two_weeks_ago.timestamp()))

    # Generate 100 slot timestamps with 5 minute intervals
    slot_timestamps = [slot_timestamp + i * 300 for i in range(100)]

    # generate IDS with 0x18f54cc21b7a2fdd011bea06bba7801b280e3151-slot_timestamp
    generated_ids = [
        f"0x18f54cc21b7a2fdd011bea06bba7801b280e3151-{slot}" for slot in slot_timestamps
    ]

    slots_list = []

    for i in range(100):
        slot = Slot(
            ID=generated_ids[i],
            timestamp=slot_timestamps[i],
            slot=slot_timestamps[i],
            truevalue=True,
            roundSumStakesUp=150.0,
            roundSumStakes=100.0,
        )
        slots_list.append(slot)

    contracts_mock = ["0x18f54cc21b7a2fdd011bea06bba7801b280e3151"]
    test_json_file_path = str(tmpdir.join("test.json"))

    def mock_fetch_all_slots(
        start_ts_param, end_ts_param, contracts, first, skip, network
    ):
        return slots_list

    def mock_get_all_contract_ids_by_owner(owner_address, network):
        return contracts_mock

    with patch("pdr_backend.accuracy.app.JSON_FILE_PATH", test_json_file_path):
        with patch(
            "pdr_backend.accuracy.app.get_all_contract_ids_by_owner",
            mock_get_all_contract_ids_by_owner,
        ):
            with patch(
                "pdr_backend.accuracy.app.fetch_all_slots", mock_fetch_all_slots
            ):
                calculate_statistics_from_slots()

    # Verify
    expected_result = """[{"alias": "5m", "statistics": {"0x18f54cc21b7a2fdd011bea06bba7801b280e3151": {"token_name": "ADA/USDT", "average_accuracy": 100.0, "total_staked_yesterday": 0.0, "total_staked_today": 0.0}}}, {"alias": "1h", "statistics": {}}]"""  # pylint: disable=line-too-long
    with open(test_json_file_path, "r") as f:
        result = f.read()
        assert result == expected_result

    # Test with false values
    false_start_timestamp = slot_timestamps[-1] + 300

    # Generate 100 slot timestamps with 5 minute intervals
    false_slot_timestamps = [false_start_timestamp + i * 300 for i in range(100)]

    # generate IDS with 0x18f54cc21b7a2fdd011bea06bba7801b280e3151-slot_timestamp
    generated_ids = [
        f"0x18f54cc21b7a2fdd011bea06bba7801b280e3151-{slot}"
        for slot in false_slot_timestamps
    ]

    for i in range(100):
        slot = Slot(
            ID=generated_ids[i],
            timestamp=slot_timestamps[i],
            slot=slot_timestamps[i],
            truevalue=False,
            roundSumStakesUp=150.0,
            roundSumStakes=100.0,
        )
        slots_list.append(slot)

    def mock_fetch_all_slots_with_false_results(
        start_ts_param, end_ts_param, contracts, first, skip, network
    ):
        return slots_list

    test_json_file_path = str(tmpdir.join("test.json"))
    with patch("pdr_backend.accuracy.app.JSON_FILE_PATH", test_json_file_path):
        with patch(
            "pdr_backend.accuracy.app.get_all_contract_ids_by_owner",
            mock_get_all_contract_ids_by_owner,
        ):
            with patch(
                "pdr_backend.accuracy.app.fetch_all_slots",
                mock_fetch_all_slots_with_false_results,
            ):
                calculate_statistics_from_slots()

    expected_result = """[{"alias": "5m", "statistics": {"0x18f54cc21b7a2fdd011bea06bba7801b280e3151": {"token_name": "ADA/USDT", "average_accuracy": 50.0, "total_staked_yesterday": 0.0, "total_staked_today": 0.0}}}, {"alias": "1h", "statistics": {}}]"""  # pylint: disable=line-too-long

    with open(test_json_file_path, "r") as f:
        result = f.read()
        assert result == expected_result
