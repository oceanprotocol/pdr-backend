import plotly.graph_objects as go

# Hex color codes for varying shades of purple
colors = [
    "#dab3ff",  # light purple
    "#c299ff",  # medium light purple
    "#a366ff",  # medium purple
    "#8c33ff",  # medium dark purple
    "#6600cc",  # dark purple
    "#4d0099"   # very dark purple
]

# Traces from ClassifLinearElasticNet and ClassifLinearLasso
all_traces = [
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1072.5618, 1072.48335, 1072.60465],
        name="ElasticNet: Sigmoid & Autoregressive_n = 1",
        marker=dict(color=colors[0]),
        customdata=["Sigmoid", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1408.35425, 1405.69085, 1403.5482],
        name="Lasso: Sigmoid & Autoregressive_n = 1",
        marker=dict(color=colors[1]),
        customdata=["Sigmoid", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1947.8634, 1947.7629, 1947.83355],
        name="ElasticNet: None & Autoregressive_n = 1",
        marker=dict(color=colors[2]),
        customdata=["None", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[2004.16795, 1996.9361, 2005.09355],
        name="Lasso: None & Autoregressive_n = 1",
        marker=dict(color=colors[3]),
        customdata=["None", "1"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[1955.451, 1948.1904, 1947.92045],
        name="ElasticNet: None & Autoregressive_n = 2",
        marker=dict(color=colors[4]),
        customdata=["None", "2"]
    ),
    go.Scatter(
        x=[1000, 2000, 5000],
        y=[2010.10125, 2010.1781, 2005.73015],
        name="Lasso: None & Autoregressive_n = 2",
        marker=dict(color=colors[5]),
        customdata=["None", "2"]
    )
]

# Define the layout
layout = go.Layout(
    title=dict(
        text="Highest Predictoor Profit Benchmarks for Calibrations of ClassifLinearLasso & ClassifLinearElasticNet Models",
        x=0.5  # Center the title
    ),
    xaxis=dict(
        title="Max_N_Train",
        tickvals=[1000, 2000, 5000],
        ticktext=["1000", "2000", "5000"]
    ),
    yaxis=dict(
        title="Predictoor Profit (OCEAN)",
        tickmode='linear',
        dtick=100,
        range=[750, 2250],
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
            text="Traces Sorted by Ascending Predictoor Profit"
        )
    ),
    hovermode='closest'
)

# Create and display the plot
fig = go.Figure(data=all_traces, layout=layout)
fig.show()

