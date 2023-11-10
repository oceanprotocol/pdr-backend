import os
import csv


def write_prediction_csv(all_predictions, csv_output_dir):
    if not os.path.exists(csv_output_dir):
        os.makedirs(csv_output_dir)

    data = {}
    for prediction in all_predictions:
        key = (
            prediction.pair.replace("/", "-") + prediction.timeframe + prediction.source
        )
        if key not in data:
            data[key] = []
        data[key].append(prediction)

    for key, predictions in data.items():
        predictions.sort(key=lambda x: x.timestamp)
        filename = os.path.join(csv_output_dir, key + ".csv")
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
