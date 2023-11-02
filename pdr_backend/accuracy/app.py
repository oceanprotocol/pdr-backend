import threading
import json
from flask import Flask, jsonify

from pdr_backend.util.subgraph_predictions import get_all_contracts
from pdr_backend.accuracy.utils.get_start_end_params import get_start_end_params
from pdr_backend.util.subgraph_slot import calculate_statistics_for_all_assets
from pdr_backend.util.subgraph_predictions import get_contract_informations

app = Flask(__name__)
JSON_FILE_PATH = "pdr_backend/accuracy/output/accuracy_data.json"


def save_statistics_to_file():
    while True:
        try:
            network_param = "mainnet"  # or 'testnet' depending on your preference

            contract_addresses = get_all_contracts(
                "0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703", network_param
            )

            contract_information = get_contract_informations(
                contract_addresses, network_param
            )

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

            output = []

            print("contract_information", len(contract_information))
            for statistic_type in statistic_types:

                seconds_per_epoch = statistic_type["seconds_per_epoch"]
                contracts = list(
                    filter(
                        lambda item, spe=seconds_per_epoch: int(item["seconds_per_epoch"]) == spe,
                        contract_information,
                    )
                )

                start_ts_param, end_ts_param = get_start_end_params(seconds_per_epoch)

                contract_ids = [contract["id"] for contract in contracts]
                print("contract_ids", len(contract_ids))

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
