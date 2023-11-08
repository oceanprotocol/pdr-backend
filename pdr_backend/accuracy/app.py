import threading
import json
from datetime import datetime, timedelta
from typing import Tuple
from enforce_typing import enforce_types
from flask import Flask, jsonify

from pdr_backend.util.subgraph_predictions import get_all_contract_ids_by_owner
from pdr_backend.util.subgraph_slot import calculate_statistics_for_all_assets
from pdr_backend.util.subgraph_predictions import fetch_contract_id_and_spe

app = Flask(__name__)
JSON_FILE_PATH = "pdr_backend/accuracy/output/accuracy_data.json"


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
        timedelta(weeks=2)
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

    contract_information = fetch_contract_id_and_spe(contract_addresses, network_param)

    while True:
        try:
            output = []

            for statistic_type in statistic_types:
                seconds_per_epoch = statistic_type["seconds_per_epoch"]
                contracts = list(
                    filter(
                        lambda item, spe=seconds_per_epoch: int(
                            item["seconds_per_epoch"]
                        )
                        == spe,
                        contract_information,
                    )
                )

                start_ts_param, end_ts_param = calculate_timeframe_timestamps(
                    statistic_type["alias"]
                )

                contract_ids = [contract["id"] for contract in contracts]

                # Get statistics for all contracts
                statistics = calculate_statistics_for_all_assets(
                    contract_ids, start_ts_param, end_ts_param, network_param
                )

                output.append(
                    {
                        "alias": statistic_type["alias"],
                        "statistics": statistics,
                    }
                )

            with open(JSON_FILE_PATH, "w") as f:
                json.dump(output, f)

            print("Data saved to JSON")
        except Exception as e:
            print("Error:", e)

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
            return jsonify(data)
    except Exception as e:
        # abort(500, description=str(e))
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


if __name__ == "__main__":
    # Start the thread to save predictions data to a file every 5 minutes
    thread = threading.Thread(target=save_statistics_to_file)
    thread.start()

    app.run(debug=True)
