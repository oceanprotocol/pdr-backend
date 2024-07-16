import pandas as pd
import plotly.graph_objects as go

file_path = "[Enter Your File Path to CSV Data]"

# Function to load data from CSV and filter it
def load_data_from_csv(file_path):
    # Read the CSV file, making sure that 'None' is not interpreted as NaN
    df = pd.read_csv(file_path, na_values=[''])
    
    # Replace NaN values in the 'Classifier' column with the string 'None'
    df['Classifier'] = df['Classifier'].fillna('None')
    
    # Filter rows without and with 'ETH' in the 'predictoor_ss.predict_train_feedsets' column
    df_without_eth = df[~df['predictoor_ss.predict_train_feedsets'].str.contains('ETH')].copy()
    df_with_eth = df[df['predictoor_ss.predict_train_feedsets'].str.contains('ETH')].copy()
    
    # Define color mapping for classifiers
    color_mapping = {
        'Sigmoid': 'orange',
        'Isotonic': 'blue',
        'None': 'fuchsia'
    }
    
    # Add color column based on classifier
    df_without_eth['Color'] = df_without_eth['Classifier'].map(color_mapping)
    df_with_eth['Color'] = df_with_eth['Classifier'].map(color_mapping)
    
    return df_without_eth, df_with_eth

# Function to generate traces from the DataFrame
def generate_traces(df, selected_classifiers, selected_autoregressives, y_column):
    traces = []
    for classifier in selected_classifiers:
        for autoregressive in selected_autoregressives:
            filtered_df = df[(df['Classifier'] == classifier) & (df['predictoor_ss.aimodel_data_ss.autoregressive_n'] == int(autoregressive))]
            print(f"Processing {classifier} with Autoregressive_n = {autoregressive}")
            print(f"Filtered DataFrame for {classifier} & Autoregressive_n = {autoregressive}:")
            print(filtered_df)
            if not filtered_df.empty:
                traces.append(
                    go.Scatter(
                        x=filtered_df['predictoor_ss.aimodel_data_ss.max_n_train'],
                        y=filtered_df[y_column],
                        name=f"{classifier} & Autoregressive_n = {autoregressive}",
                        marker=dict(color=filtered_df['Color'].iloc[0]),
                        customdata=[classifier, autoregressive]
                    )
                )
            else:
                print(f"No data for {classifier} with Autoregressive_n = {autoregressive}")
    return traces

# Define the layout
layout = go.Layout(
    title="ClassifLinearRidge Predictoor Profit Benchmarks for Three Calibrations, # of Training Samples, and Autoregressive_n",
    xaxis=dict(
        title="Max_N_Train",
        tickvals=[1000, 2000, 5000],
        ticktext=["1000", "2000", "5000"]
    ),
    yaxis=dict(
        title="Predictoor Profit (OCEAN)",
        tickmode='auto',
        showgrid=True,
        tickfont=dict(size=10),
        automargin=True
    ),
    margin=dict(
        l=70,
        r=20,
        t=60,
        b=40
    ),
    showlegend=True,
    hovermode='closest'
)

# Function to update the plot based on selected classifiers, autoregressives, and the y_column to plot
def plot_data(file_path, selected_classifiers, selected_autoregressives, y_column):
    df_without_eth, df_with_eth = load_data_from_csv(file_path)
    
    # Plot without ETH
    traces_without_eth = generate_traces(df_without_eth, selected_classifiers, selected_autoregressives, y_column)
    fig_without_eth = go.Figure(data=traces_without_eth, layout=layout)
    fig_without_eth.update_layout(title=f"ClassifLinearRidge Predictoor Benchmarks (Trained with BTC-USDT Data) - {y_column}")
    fig_without_eth.show()
    
    # Plot with ETH
    traces_with_eth = generate_traces(df_with_eth, selected_classifiers, selected_autoregressives, y_column)
    fig_with_eth = go.Figure(data=traces_with_eth, layout=layout)
    fig_with_eth.update_layout(title=f"ClassifLinearRidge Predictoor Benchmarks (Trained with BTC-USDT & ETH-USDT Data) - {y_column}")
    fig_with_eth.show()

# Example usage
selected_classifiers = ["None", "Isotonic", "Sigmoid"]
selected_autoregressives = ["1", "2"]
y_column = 'pdr_profit_OCEAN'  # Column to plot: 'f1', 'pdr_profit_OCEAN', or 'trader_profit_USD'
plot_data(file_path, selected_classifiers, selected_autoregressives, y_column)
