from itertools import product
from typing import Dict, Union, List, Tuple
import plotly.graph_objects as go
from enforce_typing import enforce_types
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def process_payouts_for_pair(payouts: List[dict]) -> tuple:
    """
    Process payouts data for a given predictor and feed.
    Args:
        payouts (list): List of payouts data.
    Returns:
        tuple: Tuple of slots, accuracies, profits, and stakes.
    """
    slots, accuracies, profits, stakes = [], [], [], []
    profit = predictions = correct_predictions = 0

    for p in payouts:
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
def process_payout_information(
    payouts: List[dict], predictoors: List[str], feeds: List[Dict]
) -> Dict:
    if not payouts:
        return {}

    results = {}

    for predictor, feed in product(predictoors, feeds):
        slots, accuracies, profits, stakes = process_payouts_for_pair(
            # payouts for a given predictor and feed
            [p for p in payouts if predictor in p["ID"] or feed["contract"] in p["ID"]]
        )

        if not slots:
            continue

        short_name = f"{predictor[:5]} - {feed['feed_name']}"
        results[short_name] = (slots, accuracies, profits, stakes)

    return results


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
    payouts: List, feeds: List, predictoors: List[str]
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

    processed_payouts = process_payout_information(payouts, predictoors, feeds)

    for label, payout in processed_payouts.items():
        slots, accuracies, profits, stakes = payout
        accuracy_scatters.append(
            go.Scatter(x=slots, y=accuracies, mode="lines", name=label)
        )
        profit_scatters.append(go.Scatter(x=slots, y=profits, mode="lines", name=label))
        stakes_scatters.append(go.Bar(x=slots, y=stakes, name=label, width=5))

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
