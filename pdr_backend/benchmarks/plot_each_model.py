"""

Takes a Simulation's CSV data and plots each model by calibration.

"""

import os
import pandas as pd
import plotly.graph_objects as go  # type: ignore

# Example file path
FILE_PATH = (
    "/Users/abc/Dev/ClassifLinearElasticNet Balanced_50kIterations_Summary.csv"
)


def load_data_from_csv(file_path):
    """
    Loads Sim data from a CSV file into 2 dataframes.

    Returns:
        Two dataframes, one with ETH data and one without.
    """
    # Function body
    df = pd.read_csv(file_path, na_values=[""])
    df["Calibration"] = df["Calibration"].fillna("None")
    model_name = os.path.basename(file_path).split("_")[0]
    df["Model"] = model_name
    df_without_eth = df[
        ~df["predictoor_ss.predict_train_feedsets"].str.contains("ETH")
    ].copy()
    df_with_eth = df[
        df["predictoor_ss.predict_train_feedsets"].str.contains("ETH")
    ].copy()
    color_mapping = {"Sigmoid": "orange", "Isotonic": "blue", "None": "fuchsia"}
    df_without_eth["Color"] = df_without_eth["Calibration"].map(color_mapping)
    df_with_eth["Color"] = df_with_eth["Calibration"].map(color_mapping)
    print(
        f"Data Types:\n{df.dtypes}"
    )  # Check the data types to ensure they are read correctly
    return df_without_eth, df_with_eth


def generate_traces(df, calibrations, autoregressive_n, y_column):
    """
    Generates traces for the given dataframes to be plotted.

    Returns:
        List of traces.
    """
    traces = []
    for calibration in calibrations:
        for autoregressive in autoregressive_n:
            filtered_df = df[
                (df["Calibration"] == calibration)
                & (
                    df["predictoor_ss.aimodel_data_ss.autoregressive_n"]
                    == int(autoregressive)
                )
            ]
            if not filtered_df.empty:
                traces.append(
                    go.Scatter(
                        x=filtered_df["predictoor_ss.aimodel_data_ss.max_n_train"],
                        y=filtered_df[y_column],
                        name=f"{calibration} & Autoregressive_n = {autoregressive}",
                        marker={"color": filtered_df["Color"].iloc[0]},
                        customdata=[calibration, autoregressive],
                    )
                )
            else:
                print(
                    f"No data for {calibration} with Autoregressive_n = {autoregressive}"
                )
    return traces


layout = {
    "title": {"text": "Traces Sorted by Ascending Predictoor Profit"},
    "xaxis": {
        "title": "Max_N_Train",
        "tickvals": [1000, 2000, 5000],
        "ticktext": ["1000", "2000", "5000"],
    },
    "margin": {"l": 70, "r": 20, "t": 60, "b": 40},
    "showlegend": True,
    "legend": {"title": {"text": "Traces Sorted by Ascending Predictoor Profit"}},
    "hovermode": "closest",
}


def plot_data(filename, calibration, autoregressive_n, y_column):
    """
    Plots the data from the given CSV file.

    Returns:
        Two plots, one with ETH data and one without.
    """
    df_without_eth, df_with_eth = load_data_from_csv(filename)
    traces_without_eth = generate_traces(
        df_without_eth, calibration, autoregressive_n, y_column
    )
    yaxis_title = (
        "Predictoor Profit (OCEAN)"
        if y_column == "pdr_profit_OCEAN"
        else "Trader Profit (USD)"
    )
    fig_without_eth = go.Figure(data=traces_without_eth, layout=layout)
    fig_without_eth.update_layout(
        title=f"{df_without_eth['Model'].iloc[0]} - "
        + f"Predictoor Profit Benchmarks (Trained with BTC-USDT Data) - {y_column}",
        yaxis_title=yaxis_title,
    )
    fig_without_eth.show()
    traces_with_eth = generate_traces(
        df_with_eth, selected_calibrations, selected_autoregressives, y_column
    )
    fig_with_eth = go.Figure(data=traces_with_eth, layout=layout)
    fig_with_eth.update_layout(
        title=f"{df_with_eth['Model'].iloc[0]} - "
        + f"Predictoor Profit Benchmarks (Trained with BTC-USDT & ETH-USDT Data) - {y_column}",
        yaxis_title=yaxis_title,
    )
    fig_with_eth.show()


selected_calibrations = ["None", "Isotonic", "Sigmoid"]
selected_autoregressives = ["1", "2"]
Y_COLUMN = "pdr_profit_OCEAN"  # Example Column to plot: 'pdr_profit_OCEAN' or 'trader_profit_USD'
plot_data(FILE_PATH, selected_calibrations, selected_autoregressives, Y_COLUMN)
