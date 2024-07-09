from itertools import product
from typing import Union, List, Tuple, Optional
import plotly.graph_objects as go
from enforce_typing import enforce_types
from pdr_backend.util.time_types import UnixTimeS


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
    return go.Bar(x=x_data, y=y_data, name=name, width=1)


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
        if not (predictor in p["ID"] and feed in p["ID"]):
            continue

        predictions += 1
        profit_change = max(p["payout"], 0) - p["stake"]
        profit += profit_change
        correct_predictions += p["payout"] > 0

        slots.append(p["slot"])
        accuracies.append((correct_predictions / predictions) * 100)
        profits.append(profit)
        stakes.append(p["stake"])
    slot_in_date_format = [
        UnixTimeS(ts).to_milliseconds().to_dt().strftime("%m-%d %H:%M") for ts in slots
    ]
    return slot_in_date_format, accuracies, profits, stakes


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
    legend_config = (
        {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        }
        if show_legend
        else {}
    )

    fig.update_layout(
        title=title,
        yaxis_title=yaxis_title,
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        showlegend=show_legend,
        xaxis_nticks=4,
        bargap=0.1,
        barmode="stack",
        legend=legend_config,
    )
    return fig


@enforce_types
def get_figures(
    payouts: Optional[List], feeds: List, predictoors: List[str]
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
        for predictor, feed in product(predictoors, feeds):
            slots, accuracies, profits, stakes = process_payouts(
                payouts, predictor, feed["contract"]
            )
            if slots:
                short_name = f"{predictor[:5]} - {feed['feed_name']}"
                accuracy_scatters.append(
                    go.Scatter(x=slots, y=accuracies, mode="lines", name=short_name)
                )
                profit_scatters.append(
                    go.Scatter(x=slots, y=profits, mode="lines", name=short_name)
                )
                stakes_scatters.append(create_bar(short_name, slots, stakes))

    if not accuracy_scatters:
        accuracy_scatters.append(go.Scatter(x=[], y=[], mode="lines", name="accuracy"))
    if not profit_scatters:
        profit_scatters.append(go.Scatter(x=[], y=[], mode="lines", name="profit"))
    if not stakes_scatters:
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
