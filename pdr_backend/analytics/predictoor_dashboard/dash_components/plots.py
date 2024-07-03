import plotly.graph_objects as go
from enforce_typing import enforce_types
from typing import Union, List, Tuple, Optional


@enforce_types
def create_scatter(
    name: str, x_data: List[float], y_data: List[int], mode="lines"
) -> go.Scatter:
    """Create a scatter plot with the given data.
    Args:
        name (str): Name of the trace.
        x_data (List): List of x values.
        y_data (List): List of y values.
        mode (str): Plot mode. Default is 'lines'.
    Returns:
        go.Scatter: Scatter plot trace.
    """
    return go.Scatter(x=x_data, y=y_data, mode=mode, name=name)


@enforce_types
def create_bar(name: str, x_data: List[float], y_data: List[int]) -> go.Bar:
    """Create a bar plot with the given data.
    Args:
        name (str): Name of the trace.
        x_data (list): List of x values.
        y_data (list): List of y values.
    Returns:
        go.Bar: Bar plot trace.
    """
    return go.Bar(x=x_data, y=y_data, name=name)


@enforce_types
def process_payouts(payouts: List[dict], predictor: str, feed: str) -> tuple:
    """
    Process payouts data for a given predictor and feed.
    Args:
        payouts (list): List of payouts data.
        predictor (str): Predictor address.
        feed (str): Feed contract address.
    Returns:
        tuple: Tuple of slots, accuracies, profits, and stakes.
    """
    slots, accuracies, profits, stakes = [], [], [], []
    profit = predictions = correct_predictions = 0

    for p in payouts:
        if predictor in p["ID"] and feed in p["ID"]:
            predictions += 1
            profit_change = p["payout"] - p["stake"] if p["payout"] > 0 else -p["stake"]
            profit += profit_change
            correct_predictions += p["payout"] > 0

            slots.append(p["slot"] / 1000)
            accuracies.append((correct_predictions / predictions) * 100)
            profits.append(profit)
            stakes.append(p["stake"])
    return slots, accuracies, profits, stakes


@enforce_types
def create_figure(
    data_traces: List[Union[go.Scatter, go.Bar]],
    title: str,
    yaxis_title: str,
    show_legend: bool = True,
):
    """
    Create a figure with the given data traces.
    Args:
        data_traces (list): List of data traces.
        title (str): Figure title.
        yaxis_title (str): Y-axis title.
        show_legend (bool): Show legend. Default is True.
    Returns:
        go.Figure: Plotly figure.
    """
    fig = go.Figure(data_traces)
    fig.update_layout(
        title=title,
        yaxis_title=yaxis_title,
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        showlegend=show_legend,
        legend=(
            {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            }
            if show_legend
            else {}
        ),
    )
    return fig


@enforce_types
def get_figures(
    payouts: Optional[List], feeds: List[str], predictoors: List[str]
) -> Tuple[go.Figure, go.Figure, go.Figure]:
    """
    Get figures for accuracy, profit, and costs.
    Args:
        payouts (list): List of payouts data.
        feeds (list): List of feeds data.
        predictoors (list): List of predictoors data.
    Returns:
        tuple: Tuple of accuracy, profit, and costs figures.
    """
    accuracy_scatters, profit_scatters, stakes_scatters = [], [], []

    if payouts:
        for predictor in predictoors:
            for feed in feeds:
                slots, accuracies, profits, stakes = process_payouts(
                    payouts, predictor, feed["contract"]
                )
                if slots:
                    short_name = f"{predictor[:5]} - {feed['feed_name']}"
                    accuracy_scatters.append(
                        create_scatter(short_name, slots, accuracies)
                    )
                    profit_scatters.append(create_scatter(short_name, slots, profits))
                    stakes_scatters.append(create_bar(short_name, slots, stakes))
    else:
        accuracy_scatters.append(create_scatter("accuracy", [], []))
        profit_scatters.append(create_scatter("profit", [], []))
        stakes_scatters.append(create_bar("stakes", [], []))

    fig_accuracy = create_figure(
        accuracy_scatters, "Accuracy", "'%' accuracy over time"
    )
    fig_profit = create_figure(
        profit_scatters, "Profit", "OCEAN profit over time", show_legend=False
    )
    fig_costs = create_figure(
        stakes_scatters, "Costs", "Stake (OCEAN) at a time", show_legend=False
    )

    return fig_accuracy, fig_profit, fig_costs
