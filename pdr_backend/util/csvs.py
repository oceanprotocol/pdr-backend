import os
import csv
from typing import List, Dict
from io import TextIOWrapper

from enforce_typing import enforce_types
from pdr_backend.util.subgraph_predictions import Prediction


@enforce_types
def create_csv_header_columns(columns: List[str], file: TextIOWrapper):
    writer = csv.writer(file)
    writer.writerow(columns)
    return writer

@enforce_types
def generate_csv_file_path(csv_output_dir: str, key: str) -> str:
    return os.path.join(
        csv_output_dir,
        key + ".csv",
    )

@enforce_types
def generate_prediction_data_structure(
    predictions: List[Prediction]) -> Dict[str, List[Prediction]]:

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
def write_prediction_csv(all_predictions: List[Prediction], csv_output_dir: str):
    check_and_create_dir(csv_output_dir)

    data = generate_prediction_data_structure(all_predictions)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = generate_csv_file_path(csv_output_dir, key)
        with open(filename, "w", newline="") as file:
            writer = create_csv_header_columns(
                ["Predicted Value", "True Value", "Timestamp", "Stake", "Payout"], file)

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
def write_analysis_prediction(all_predictions: List[Prediction], csv_output_dir: str):
    check_and_create_dir(csv_output_dir)

    data = generate_prediction_data_structure(all_predictions)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = generate_csv_file_path(csv_output_dir, key)
        with open(filename, "w", newline="") as file:
            writer = create_csv_header_columns(
                [
                    "PredictionID", 
                    "Timestamp",
                    "Submit Timestamp",
                    "Stake",
                    "Wallet",
                    "Payout",
                    "True Value",
                    "Predicted Value"
                ], file)

            for prediction in predictions:
                writer.writerow(
                    [
                        prediction.predictionId,
                        prediction.timestamp,
                        prediction.submittimestamp,
                        prediction.stake,
                        prediction.user,
                        prediction.payout,
                        prediction.trueval,
                        prediction.prediction,
                    ]
                )
        print(f"CSV file '{filename}' created successfully.")
