import plotly.graph_objects as go

traces = [
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[2004.16795, 1996.9361, 2005.09355],
        name="None & Autoregressive_n = 1",
        marker=dict(color="fuchsia"),
        customdata=["None", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[2010.10125, 2010.1781, 2005.73015],
        name="None & Autoregressive_n = 2",
        marker=dict(color="fuchsia"),
        customdata=["None", "2"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[614.2339, 609.4145, 587.32865],
        name="Isotonic & Autoregressive_n = 1",
        marker=dict(color="blue"),
        customdata=["Isotonic", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[610.6582, 593.16395, 603.0196],
        name="Isotonic & Autoregressive_n = 2",
        marker=dict(color="blue"),
        customdata=["Isotonic", "2"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1408.35425, 1405.69085, 1403.5482],
        name="Sigmoid & Autoregressive_n = 1",
        marker=dict(color="orange"),
        customdata=["Sigmoid", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1407.12415, 1413.144, 1410.46985],
        name="Sigmoid & Autoregressive_n = 2",
        marker=dict(color="orange"),
        customdata=["Sigmoid", "2"]
    )
]

# Define the layout
layout = go.Layout(
    title="ClassifLinearLasso Predictoor Profit Benchmarks for Three Calibrations, # of Training Samples, and Autoregressive_n",
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
        range=[250, 2250],
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

