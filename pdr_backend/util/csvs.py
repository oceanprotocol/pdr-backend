import os
import csv
from typing import List, Dict

from enforce_typing import enforce_types
from pdr_backend.util.subgraph_predictions import Prediction


@enforce_types
def get_plots_dir(pq_dir: str):
    plots_dir = os.path.join(pq_dir, "plots")
    if not os.path.exists(plots_dir):
        os.makedirs(plots_dir)
    return plots_dir


@enforce_types
def key_csv_filename_with_dir(csv_output_dir: str, key: str) -> str:
    return os.path.join(
        csv_output_dir,
        key + ".csv",
    )


@enforce_types
def generate_prediction_data_structure(
    predictions: List[Prediction],
) -> Dict[str, List[Prediction]]:
    data: Dict[str, List[Prediction]] = {}
    for prediction in predictions:
        key = (
            prediction.pair.replace("/", "-") + prediction.timeframe + prediction.source
        )
        if key not in data:
            data[key] = []
        data[key].append(prediction)
    return data


@enforce_types
def check_and_create_dir(dir_path: str):
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)


@enforce_types
def save_prediction_csv(all_predictions: List[Prediction], csv_output_dir: str):
    check_and_create_dir(csv_output_dir)

    data = generate_prediction_data_structure(all_predictions)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = key_csv_filename_with_dir(csv_output_dir, key)
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow(
                ["Predicted Value", "True Value", "Timestamp", "Stake", "Payout"]
            )

            for prediction in predictions:
                writer.writerow(
                    [
                        prediction.prediction,
                        prediction.trueval,
                        prediction.timestamp,
                        prediction.stake,
                        prediction.payout,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")


@enforce_types
def save_analysis_csv(all_predictions: List[Prediction], csv_output_dir: str):
    check_and_create_dir(csv_output_dir)

    data = generate_prediction_data_structure(all_predictions)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = key_csv_filename_with_dir(csv_output_dir, key)
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "PredictionID",
                    "Timestamp",
                    "Slot",
                    "Stake",
                    "Wallet",
                    "Payout",
                    "True Value",
                    "Predicted Value",
                ]
            )

            for prediction in predictions:
                writer.writerow(
                    [
                        prediction.id,
                        prediction.timestamp,
                        prediction.slot,
                        prediction.stake,
                        prediction.user,
                        prediction.payout,
                        prediction.trueval,
                        prediction.prediction,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")
