#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

import pandas as pd


def read_files_from_directory(directory):
    file_data = {}
    if os.path.isdir(directory):
        for filename in os.listdir(directory):
            if not filename.endswith(".csv") and not filename.endswith(".parquet"):
                continue
            filepath = os.path.join(directory, filename)
            df = (
                pd.read_csv(filepath)
                if filename.endswith(".csv")
                else pd.read_parquet(filepath)
            )
            if hasattr(df, "close") and hasattr(df, "timestamp"):
                file_data[filename.split(".")[0]] = {
                    "close_data": df["close"],
                    "timestamps": pd.to_datetime(df["timestamp"], unit="ms"),
                }
    return file_data


def filter_file_data_by_date(file_data, start_date, end_date):
    """
    Filter file_data to include only the close_data and timestamps between start_date and end_date.

    Parameters:
    - file_data (dict): A dictionary with keys "close_data" and "timestamps".
    - start_date (str or pd.Timestamp): The start date for filtering.
    - end_date (str or pd.Timestamp): The end date for filtering.

    Returns:
    - dict: A dictionary with filtered "close_data" and "timestamps".
    """
    # Ensure start_date and end_date are pandas timestamps
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Create a DataFrame from the file_data
    df = pd.DataFrame(
        {
            "close_data": file_data["close_data"],
            "timestamps": pd.to_datetime(
                file_data["timestamps"]
            ),  # Ensure timestamps are datetime objects
        }
    )

    # Filter the DataFrame based on the date range
    mask = (df["timestamps"] >= start_date) & (df["timestamps"] <= end_date)
    filtered_df = df.loc[mask]

    # Convert the filtered DataFrame back to dictionary format
    filtered_file_data = {
        "close_data": filtered_df["close_data"].tolist(),
        "timestamps": filtered_df["timestamps"].tolist(),
    }

    return filtered_file_data
