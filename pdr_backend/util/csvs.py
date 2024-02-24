import csv
import logging
import os
from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.subgraph.subgraph_predictions import Prediction

logger = logging.getLogger("csvs")


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
def _save_prediction_csv(
    all_predictions: List[Prediction],
    csv_output_dir: str,
    headers_attrs: dict,
):
    if not os.path.isdir(csv_output_dir):
        os.makedirs(csv_output_dir)

    data = generate_prediction_data_structure(all_predictions)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = key_csv_filename_with_dir(csv_output_dir, key)
        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)

            writer.writerow(headers_attrs.keys())

            for prediction in predictions:
                writer.writerow(
                    [
                        getattr(prediction, attribute_name)
                        for attribute_name in headers_attrs.values()
                    ]
                )

        logger.info("CSV file '%s' created successfully.", filename)


def save_prediction_csv(all_predictions: List[Prediction], csv_output_dir: str):
    _save_prediction_csv(
        all_predictions,
        csv_output_dir,
        {
            "Predicted Value": "prediction",
            "True Value": "trueval",
            "Timestamp": "timestamp",
            "Stake": "stake",
            "Payout": "payout",
        },
    )


@enforce_types
def save_analysis_csv(all_predictions: List[Prediction], csv_output_dir: str):
    _save_prediction_csv(
        all_predictions,
        csv_output_dir,
        {
            "PredictionID": "ID",
            "Timestamp": "timestamp",
            "Slot": "slot",
            "Stake": "stake",
            "Wallet": "user",
            "Payout": "payout",
            "True Value": "trueval",
            "Predicted Value": "prediction",
        },
    )
