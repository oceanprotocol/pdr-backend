import pandas as pd
import plotly.graph_objects as go
import os

# Function to load and process data from a CSV file
def load_and_process_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path, na_values=[''])
    
    # Replace NaN values in the 'Classifier' column with the string 'None'
    df['Classifier'] = df['Classifier'].fillna('None')
    
    # Extract the model name from the file name
    model_name = os.path.basename(file_path).split('_')[0]  # Adjust this if your naming convention is different
    df['Model'] = model_name
    
    return df

# Function to get the top 3 most profitable traces from the combined DataFrame
def get_top_traces_combined(df, y_column):
    # Group by model, classifier, and autoregressive_n and find the max value for the y_column for each group
    grouped = df.groupby(['Model', 'Classifier', 'predictoor_ss.aimodel_data_ss.autoregressive_n'])
    max_profits = grouped[y_column].max().reset_index()
    
    # Sort by the y_column and select the top 3
    top_traces = max_profits.nlargest(3, y_column)
    
    # Get all rows for the selected top traces
    top_trace_indices = top_traces[['Model', 'Classifier', 'predictoor_ss.aimodel_data_ss.autoregressive_n']]
    top_trace_full_df = df.merge(top_trace_indices, on=['Model', 'Classifier', 'predictoor_ss.aimodel_data_ss.autoregressive_n'])
    
    return top_trace_full_df

# Function to generate traces for plotting
def generate_traces(df, green_shades, y_column):
    traces = []
    
    # Sort by maximum y_column value to apply colors in ascending order
    sorted_groups = df.groupby(['Model', 'Classifier', 'predictoor_ss.aimodel_data_ss.autoregressive_n']).max(y_column).reset_index()
    sorted_groups = sorted_groups.sort_values(y_column)
    
    for (index, row) in sorted_groups.iterrows():
        model = row['Model']
        classifier = row['Classifier']
        autoregressive = row['predictoor_ss.aimodel_data_ss.autoregressive_n']
        color = green_shades.pop(0) if green_shades else 'green'  # Fallback to green if shades run out
        group_df = df[(df['Model'] == model) & 
                      (df['Classifier'] == classifier) & 
                      (df['predictoor_ss.aimodel_data_ss.autoregressive_n'] == autoregressive)]
        traces.append(
            go.Scatter(
                x=group_df['predictoor_ss.aimodel_data_ss.max_n_train'],
                y=group_df[y_column],
                name=f"{model}: {classifier} & Autoregressive_n = {autoregressive}",
                marker=dict(color=color),
                customdata=[classifier, autoregressive],
                mode='lines+markers'
            )
        )
    
    return traces

# Function to plot data from three CSV files
def plot_data_from_csvs(file_paths, y_column):
    all_data_without_eth = []
    all_data_with_eth = []
    
    for file_path in file_paths:
        df = load_and_process_csv(file_path)
        
        # Filter rows without and with 'ETH' in the 'predictoor_ss.predict_train_feedsets' column
        df_without_eth = df[~df['predictoor_ss.predict_train_feedsets'].str.contains('ETH')].copy()
        df_with_eth = df[df['predictoor_ss.predict_train_feedsets'].str.contains('ETH')].copy()
        
        all_data_without_eth.append(df_without_eth)
        all_data_with_eth.append(df_with_eth)
    
    combined_df_without_eth = pd.concat(all_data_without_eth, ignore_index=True)
    combined_df_with_eth = pd.concat(all_data_with_eth, ignore_index=True)
    
    top_traces_df_without_eth = get_top_traces_combined(combined_df_without_eth, y_column)
    top_traces_df_with_eth = get_top_traces_combined(combined_df_with_eth, y_column)
    
    # Define shades of green for the top 3 traces
    green_shades = ['#adebad', '#66cc66', '#267326']  # Light to dark green
    
    traces_without_eth = generate_traces(top_traces_df_without_eth, green_shades.copy(), y_column)
    traces_with_eth = generate_traces(top_traces_df_with_eth, green_shades.copy(), y_column)
    
    # Define the layout
    layout = go.Layout(
        title=dict(
            text=f"Top 3 Highest {y_column} Scores",
            x=0.5  # Center the title
        ),
        xaxis=dict(
            title="Max_N_Train",
            tickvals=[1000, 2000, 5000],
            ticktext=["1000", "2000", "5000"]
        ),
        yaxis=dict(
            title=f"{y_column} Score",
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
        legend=dict(
            title=dict(
                text="Traces Sorted by Ascending F1 Score"
            )
        ),
        hovermode='closest'
    )
    
    # Create the figure and plot without ETH
    fig_without_eth = go.Figure(data=traces_without_eth, layout=layout)
    fig_without_eth.update_layout(title=f"Top 3 Highest {y_column} Scores (Trained on BTC-USDT Data)")
    fig_without_eth.show()
    
    # Create the figure and plot with ETH
    fig_with_eth = go.Figure(data=traces_with_eth, layout=layout)
    fig_with_eth.update_layout(title=f"Top 3 Highest {y_column} Scores (Trained on BTC & ETH-USDT Data)")
    fig_with_eth.show()



# Example usage
file_paths = [
    '/Users/foxylady/Dev/ClassifLinearRidge_Concatenated_Data-Summary.csv',
    '/Users/foxylady/Dev/ClassifLinearLasso_Concatenated_Data-Summary.csv',
    '/Users/foxylady/Dev/ClassifLinearElasticNet_Concatenated_Data-Summary.csv'
]

y_column = 'f1'  # Can be 'pdr_profit_OCEAN', 'trader_profit_USD' or 'f1'
plot_data_from_csvs(file_paths, y_column)