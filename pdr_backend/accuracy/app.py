import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from enforce_typing import enforce_types
from flask import Flask, jsonify

from pdr_backend.subgraph.subgraph_predictions import (
    fetch_contract_id_and_spe,
    get_all_contract_ids_by_owner,
    ContractIdAndSPE,
)
from pdr_backend.subgraph.subgraph_slot import fetch_slots, PredictSlot

app = Flask(__name__)
JSON_FILE_PATH = "pdr_backend/accuracy/output/accuracy_data.json"
SECONDS_IN_A_DAY = 86400
logger = logging.getLogger("accuracy_app")


@enforce_types
def calculate_prediction_result(
    round_sum_stakes_up: float, round_sum_stakes: float
) -> Optional[bool]:
    """
    Calculates the prediction result based on the sum of stakes.

    Args:
        round_sum_stakes_up: The summed stakes for the 'up' prediction.
        round_sum_stakes: The summed stakes for all prediction.

    Returns:
        A boolean indicating the predicted direction.
    """

    # checks for to be sure that the division is not by zero
    round_sum_stakes_up_float = float(round_sum_stakes_up)
    round_sum_stakes_float = float(round_sum_stakes)

    if round_sum_stakes_float == 0.0:
        return None

    if round_sum_stakes_up_float == 0.0:
        return False

    return (round_sum_stakes_up_float / round_sum_stakes_float) > 0.5


@enforce_types
def process_single_slot(
    slot: PredictSlot, end_of_previous_day_timestamp: int
) -> Optional[Tuple[float, float, int, int]]:
    """
    Processes a single slot and calculates the staked amounts for yesterday and today,
    as well as the count of correct predictions.

    Args:
        slot: A PredictSlot TypedDict containing information about a single prediction slot.
        end_of_previous_day_timestamp: The Unix timestamp marking the end of the previous day.

    Returns:
        A tuple containing staked amounts for yesterday, today, and the counts of correct
        predictions and slots evaluated, or None if no stakes were made today.
    """

    staked_yesterday = staked_today = 0.0
    correct_predictions_count = slots_evaluated = 0

    if float(slot.roundSumStakes) == 0.0:
        return None

    # split the id to get the slot timestamp
    timestamp = int(slot.ID.split("-")[1])  # Using dot notation for attribute access

    if (
        end_of_previous_day_timestamp - SECONDS_IN_A_DAY
        < timestamp
        < end_of_previous_day_timestamp
    ):
        staked_yesterday += float(slot.roundSumStakes)
    elif timestamp > end_of_previous_day_timestamp:
        staked_today += float(slot.roundSumStakes)

    prediction_result = calculate_prediction_result(
        slot.roundSumStakesUp, slot.roundSumStakes
    )

    if prediction_result is None:
        return (
            staked_yesterday,
            staked_today,
            correct_predictions_count,
            slots_evaluated,
        )

    true_value = slot.trueval

    if prediction_result == true_value:
        correct_predictions_count += 1

    if true_value is not None:
        slots_evaluated += 1

    return staked_yesterday, staked_today, correct_predictions_count, slots_evaluated


@enforce_types
def aggregate_statistics(
    slots: List[PredictSlot], end_of_previous_day_timestamp: int
) -> Tuple[float, float, int, int]:
    """
    Aggregates statistics across all provided slots for an asset.

    Args:
        slots: A list of PredictSlot TypedDicts containing information
            about multiple prediction slots.
        end_of_previous_day_timestamp: The Unix timestamp marking the end of the previous day.

    Returns:
        A tuple containing the total staked amounts for yesterday, today,
        and the total counts of correct predictions and slots evaluated.
    """

    total_staked_yesterday = total_staked_today = total_correct_predictions = (
        total_slots_evaluated
    ) = 0
    for slot in slots:
        slot_results = process_single_slot(slot, end_of_previous_day_timestamp)
        if slot_results:
            (
                staked_yesterday,
                staked_today,
                correct_predictions_count,
                slots_evaluated,
            ) = slot_results
            total_staked_yesterday += staked_yesterday
            total_staked_today += staked_today
            total_correct_predictions += correct_predictions_count
            total_slots_evaluated += slots_evaluated
    return (
        total_staked_yesterday,
        total_staked_today,
        total_correct_predictions,
        total_slots_evaluated,
    )


@enforce_types
def calculate_statistics_for_all_assets(
    asset_ids: List[str],
    contracts_list: List[ContractIdAndSPE],
    start_ts_param: int,
    end_ts_param: int,
    network: str = "mainnet",
) -> Dict[str, Dict[str, Any]]:
    """
    Calculates statistics for all provided assets based on
    slot data within a specified time range.

    Args:
        asset_ids: A list of asset identifiers for which statistics will be calculated.
        start_ts_param: The Unix timestamp for the start of the time range.
        end_ts_param: The Unix timestamp for the end of the time range.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dictionary mapping asset IDs to another dictionary with
        calculated statistics such as average accuracy and total staked amounts.
    """

    slots_by_asset = fetch_slots(asset_ids, start_ts_param, end_ts_param, network)

    overall_stats = {}
    for asset_id, slots in slots_by_asset.items():
        (
            staked_yesterday,
            staked_today,
            correct_predictions_count,
            slots_evaluated,
        ) = aggregate_statistics(slots, end_ts_param - SECONDS_IN_A_DAY)
        average_accuracy = (
            0
            if correct_predictions_count == 0
            else (correct_predictions_count / slots_evaluated) * 100
        )

        # filter contracts to get the contract with the current asset id
        contract_item = next(
            (
                contract_item
                for contract_item in contracts_list
                if contract_item["ID"] == asset_id
            ),
            None,
        )

        overall_stats[asset_id] = {
            "token_name": contract_item["name"] if contract_item else None,
            "average_accuracy": average_accuracy,
            "total_staked_yesterday": staked_yesterday,
            "total_staked_today": staked_today,
        }

    return overall_stats


@enforce_types
def calculate_timeframe_timestamps(contract_timeframe: str) -> Tuple[int, int]:
    """
    Calculates and returns a tuple of Unix timestamps for a start and end time
    based on a given contract timeframe. The start time is determined to be either
    2 weeks or 4 weeks in the past, depending on whether the contract timeframe is
    5 minutes or 1 hour, respectively. The end time is the current timestamp.

    Args:
        contract_timeframe (str): The contract timeframe, '5m' for 5 minutes or
                                  other string values for different timeframes.

    Returns:
        Tuple[int, int]: A tuple containing the start and end Unix timestamps.
    """

    end_ts = int(datetime.utcnow().timestamp())
    time_delta = (
        timedelta(weeks=1)
        if contract_timeframe == "5m"
        else timedelta(weeks=4)
        # timedelta(days=1)
        # if contract_timeframe == "5m"
        # else timedelta(days=1)
    )
    start_ts = int((datetime.utcnow() - time_delta).timestamp())

    return start_ts, end_ts


@enforce_types
def save_statistics_to_file():
    """
    Periodically fetches and saves statistical data to a JSON file.

    This function runs an infinite loop that every 5 minutes triggers
    data fetching for contract statistics. It uses prefetched contract
    addresses and timeframes to gather statistics and save them to a file
    in JSON format.

    If the process encounters an exception, it prints an error message and
    continues after the next interval.

    The data includes statistics for each contract based on the 'seconds per epoch'
    value defined for each statistic type.
    """

    network_param = "mainnet"  # or 'testnet' depending on your preference

    statistic_types = [
        {
            "alias": "5m",
            "seconds_per_epoch": 300,
        },
        {
            "alias": "1h",
            "seconds_per_epoch": 3600,
        },
    ]

    contract_addresses = get_all_contract_ids_by_owner(
        "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703", network_param
    )

    contracts_list_unfiltered = fetch_contract_id_and_spe(
        contract_addresses,
        network_param,
    )

    while True:
        try:
            output = []

            for statistic_type in statistic_types:
                seconds_per_epoch = statistic_type["seconds_per_epoch"]
                contracts_list = list(
                    filter(
                        lambda item, spe=seconds_per_epoch: int(
                            item["seconds_per_epoch"]
                        )
                        == spe,
                        contracts_list_unfiltered,
                    )
                )

                start_ts_param, end_ts_param = calculate_timeframe_timestamps(
                    statistic_type["alias"]
                )

                contract_ids = [contract_item["ID"] for contract_item in contracts_list]

                statistics = calculate_statistics_for_all_assets(
                    contract_ids,
                    contracts_list,
                    start_ts_param,
                    end_ts_param,
                    network_param,
                )

                output.append(
                    {
                        "alias": statistic_type["alias"],
                        "statistics": statistics,
                    }
                )

            with open(JSON_FILE_PATH, "w") as f:
                json.dump(output, f)

            logger.info("Data saved to JSON")
        except Exception as e:
            logger.error("Error: %s", e)

        threading.Event().wait(300)  # Wait for 5 minutes (300 seconds)


@enforce_types
@app.route("/statistics", methods=["GET"])
def serve_statistics_from_file():
    """
    Serves statistical data from a JSON file via a GET request.

    When a GET request is made to the '/statistics' route,
    this function reads the statistical data from the JSON file
    and returns it as a JSON response.

    If the file cannot be read or another error occurs, it returns a 500 Internal Server Error.
    """

    try:
        with open(JSON_FILE_PATH, "r") as f:
            data = json.load(f)
            response = jsonify(data)
            response.headers.add("Access-Control-Allow-Origin", "*")  # Allow any origin
            return response
    except Exception as e:
        response = jsonify({"error": "Internal Server Error", "message": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "*")  # Allow any origin
        return response, 500


if __name__ == "__main__":
    # Start the thread to save predictions data to a file every 5 minutes
    thread = threading.Thread(target=save_statistics_to_file)
    thread.start()

    app.run(debug=False)
