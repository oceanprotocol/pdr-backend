import plotly.graph_objects as go

# Plot for ClassifLinearElasticNet Predictoor Profit training with BTC-USDT data from 2024-04-01_00:00 to 2024-06-30_00:00
# Hardcoded data (will be replaced with live data from the multisim in a future update)
traces = [
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1947.8634, 1947.7629, 1947.83355],
        name="None & Autoregressive_n = 1",
        marker=dict(color="fuchsia"),
        customdata=["None", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1955.451, 1948.1904, 1947.92045],
        name="None & Autoregressive_n = 2",
        marker=dict(color="fuchsia"),
        customdata=["None", "2"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[-1525.2697, -1522.5873, -1526.5013],
        name="Isotonic & Autoregressive_n = 1",
        marker=dict(color="blue"),
        customdata=["Isotonic", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[-1524.945, -1525.7649, -1524.8911],
        name="Isotonic & Autoregressive_n = 2",
        marker=dict(color="blue"),
        customdata=["Isotonic", "2"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1072.5618, 1072.48335, 1072.60465],
        name="Sigmoid & Autoregressive_n = 1",
        marker=dict(color="orange"),
        customdata=["Sigmoid", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1072.5059, 1072.5569, 1072.59585],
        name="Sigmoid & Autoregressive_n = 2",
        marker=dict(color="orange"),
        customdata=["Sigmoid", "2"]
    )
]

# Define the layout
layout = go.Layout(
    title="ClassifLinearElasticNet Predictoor Profit Benchmarks for Three Calibrations, # of Training Samples, and Autoregressive_n",
    xaxis=dict(
        title="Max_N_Train",
        tickvals=[1000, 2000, 5000],
        ticktext=["1000", "2000", "5000"],
        #domain=[0.2, 1]
    ),
    yaxis=dict(
        title="Predictoor Profit (OCEAN)",
        tickmode='linear',
        dtick=500,
        range=[-2000, 2500],
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

# Initial plot
fig = go.Figure(data=traces, layout=layout)
# fig.show()

# Function to update the plot based on selected classifiers and autoregressives
def plot_data(selected_classifiers, selected_autoregressives):
    filtered_traces = [
        trace for trace in traces
        if trace.customdata[0] in selected_classifiers and trace.customdata[1] in selected_autoregressives
    ]
    fig = go.Figure(data=filtered_traces, layout=layout)
    fig.show()

selected_classifiers = ["None", "Isotonic", "Sigmoid"]
selected_autoregressives = ["1", "2"]
plot_data(selected_classifiers, selected_autoregressives)
