import threading
import json
from flask import Flask, jsonify

from pdr_backend.util.predictoor_stats import get_endpoint_statistics
from pdr_backend.util.subgraph_predictions import (
    get_all_predictions,
    get_all_contracts,
    FilterMode,
)
from pdr_backend.accuracy.utils.get_start_end_params import get_start_end_params

app = Flask(__name__)
JSON_FILE_PATH = "pdr_backend/accuracy/output/predictions_data.json"


def save_statistics_to_file():
    while True:
        try:
            network_param = "mainnet"  # or 'testnet' depending on your preference

            start_ts_param, end_ts_param = get_start_end_params()
            contract_addresses = get_all_contracts(
                "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703", network_param
            )
            predictions = get_all_predictions(
                start_ts_param,
                end_ts_param,
                contract_addresses,
                network_param,
                filter_mode=FilterMode.CONTRACT,
            )
            statistics = get_endpoint_statistics(predictions)

            with open(JSON_FILE_PATH, "w") as f:
                json.dump({"statistics": statistics}, f)

            print("Data saved to JSON")
        except Exception as e:
            print("Error:", e)

        threading.Event().wait(300)  # Wait for 5 minutes (300 seconds)


@app.route("/statistics", methods=["GET"])
def serve_statistics_from_file():
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
