import pandas as pd
import plotly.graph_objects as go
import os

file_paths = [
    '/Users/abc/Dev/ClassifLinearLasso_Summary.csv',
    '/Users/abc/Dev/Balanced ClassifLinearLasso_Summary.csv',
    '/Users/abc/Dev/ClassifLinearRidge_Summary.csv',
    '/Users/abc/Dev/Balanced ClassifLinearRidge_Summary.csv',
    '/Users/abc/Dev/ClassifLinearElasticNet_Summary.csv',
    '/Users/abc/Dev/Balanced ClassifLinearElasticNet_Summary.csv'
]

def load_and_process_csv(file_path):
    df = pd.read_csv(file_path, na_values=[''])
    df['Calibration'] = df['Calibration'].fillna('None')
    model_name = os.path.basename(file_path).split('_')[0]
    df['Model'] = model_name
    print(df.dtypes)  # Check the data types to ensure they are read correctly
    return df


def get_top_traces_combined(df, y_column):
    if 'Model' not in df.columns:
        raise ValueError("Model column not found in DataFrame")
    grouped = df.groupby(['Model', 'Calibration', 'predictoor_ss.aimodel_data_ss.autoregressive_n'])
    max_profits = grouped[y_column].max().reset_index()
    top_traces = max_profits.nlargest(3, y_column)
    top_trace_indices = top_traces[['Model', 'Calibration', 'predictoor_ss.aimodel_data_ss.autoregressive_n']]
    top_trace_full_df = df.merge(top_trace_indices, on=['Model', 'Calibration', 'predictoor_ss.aimodel_data_ss.autoregressive_n'])
    return top_trace_full_df

def generate_traces(df, green_shades, y_column):
    traces = []
    grouped = df.groupby(['Model', 'Calibration', 'predictoor_ss.aimodel_data_ss.autoregressive_n'])
    sorted_groups = grouped[y_column].max().reset_index().sort_values(by=y_column, ascending=False)  # Sorting highest to lowest

    temp_traces = []

    for _, row in sorted_groups.iterrows():
        group_df = grouped.get_group((row['Model'], row['Calibration'], row['predictoor_ss.aimodel_data_ss.autoregressive_n']))
        color = green_shades.pop(0)
        autoregressive_n = int(row['predictoor_ss.aimodel_data_ss.autoregressive_n'])  # Ensure it's formatted as an integer
        trace = go.Scatter(
            x=group_df['predictoor_ss.aimodel_data_ss.max_n_train'],
            y=group_df[y_column],
            name=f"{row['Model']}: {row['Calibration']} & Autoregressive_n = {autoregressive_n}",
            marker=dict(color=color),
            mode='lines+markers'
        )
        temp_traces.append(trace)

    traces.extend(reversed(temp_traces))
    return traces

def plot_data_from_csvs(file_paths, y_column, eth_column):
    all_data = []
    for file_path in file_paths:
        df = load_and_process_csv(file_path)
        all_data.append(df)

    combined_df = pd.concat(all_data, ignore_index=True)
    df_without_eth = combined_df[~combined_df[eth_column].str.contains('ETH', na=False)]
    df_with_eth = combined_df[combined_df[eth_column].str.contains('ETH', na=False)]

    plot_data(df_without_eth, y_column, "(Trained on BTC-USDT Data)")
    plot_data(df_with_eth, y_column, "(Trained on BTC & ETH-USDT Data)")

def plot_data(df, y_column, title_suffix):
    if 'Model' not in df.columns:
        raise ValueError("Model column not found in DataFrame")
    top_traces_df = get_top_traces_combined(df, y_column)
    green_shades = ['#267326', '#66cc66', '#adebad']  # Dark to light green
    traces = generate_traces(top_traces_df, green_shades.copy(), y_column)
    profit_type = "Predictoor Profit (OCEAN)" if y_column == 'pdr_profit_OCEAN' else "Trader Profit (USD)"
    layout = go.Layout(
        title=dict(text=f"Top 3 Highest {profit_type} Scores - {title_suffix}", x=0.5),
        xaxis=dict(title="Max_N_Train", tickvals=[1000, 2000, 5000], ticktext=["1000", "2000", "5000"]),
        yaxis=dict(title=profit_type, tickmode='auto', showgrid=True, tickfont=dict(size=10), automargin=True),
        margin=dict(l=70, r=20, t=60, b=40),
        showlegend=True,
        legend=dict(title=dict(text="Traces Sorted by Ascending Profit")),
        hovermode='closest'
    )
    fig = go.Figure(data=traces, layout=layout)
    fig.show()

y_column = 'trader_profit_USD'  # Can be 'pdr_profit_OCEAN' or 'trader_profit_USD'
eth_column = 'predictoor_ss.predict_train_feedsets'  # Adjust the column name as necessary
plot_data_from_csvs(file_paths, y_column, eth_column)
