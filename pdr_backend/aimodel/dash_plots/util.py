import os
import pandas as pd


def read_files_from_directory(directory):
    file_data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".csv") or filename.endswith(".parquet"):
            filepath = os.path.join(directory, filename)
            if filename.endswith(".csv"):
                df = pd.read_csv(filepath)
            else:
                df = pd.read_parquet(filepath)
            file_data[filename.split(".")[0]] = {
                "close_data": df["close"],
                "timestamps": pd.to_datetime(df["timestamp"], unit="ms"),
            }
    return file_data
