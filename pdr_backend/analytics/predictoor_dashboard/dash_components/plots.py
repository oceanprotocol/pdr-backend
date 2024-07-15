from itertools import product
from typing import List, Optional, Tuple, Union

import plotly.graph_objects as go
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def filter_payouts(payouts: List[dict], predictor: str, feed: Optional[str] = None) -> List[dict]:
    """
    Filter payouts for a given predictor and optionally a specific feed.
    """
    return [p for p in payouts if predictor in p["ID"] and (feed is None or feed in p["ID"])]

@enforce_types
def calculate_stats(filtered_payouts: List[dict]) -> Tuple[List[str], List[float], List[float], List[float], float, float, float]:
    """
    Calculate statistics from the filtered payouts.
    """
    slots, accuracies, profits, stakes = [], [], [], []
    profit = predictions = correct_predictions = 0

    for p in filtered_payouts:
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

    total_profit = profit
    total_accuracy = (correct_predictions / predictions) * 100 if predictions > 0 else 0
    avg_stake = sum(stakes) / len(stakes) if stakes else 0

    return slot_in_date_format, accuracies, profits, stakes, total_profit, total_accuracy, avg_stake

@enforce_types
def process_payouts(
    payouts: List[dict], 
    predictor: str, 
    feed: Optional[str] = None, 
    aggregate: bool = False
) -> Tuple[List[str], List[float], List[float], List[float], float, float, float]:
    """
    Process payouts data for a given predictor.
    
    Args:
        payouts (list): List of payouts data.
        predictor (str): Predictor address.
        feed (str, optional): Feed contract address. If None, process all feeds.
        aggregate (bool): If True, aggregate data across all feeds. Default is False.
        
    Returns:
        tuple: Tuple of slots, accuracies, profits, stakes, total_profit, total_accuracy, avg_stake.
    """
    filtered_payouts = filter_payouts(payouts, predictor, feed if not aggregate else None)
    return calculate_stats(filtered_payouts)

@enforce_types
def process_payouts_for_all_feeds(payouts: List[dict], predictor: str) -> Tuple[List[str], List[float], List[float], List[float], float, float, float]:
    """
    Process payouts data for a given predictor across all feeds.
    
    Args:
        payouts (list): List of payouts data.
        predictor (str): Predictor address.
        
    Returns:
        tuple: Tuple of slots, accuracies, profits, stakes, total_profit, total_accuracy, avg_stake.
    """
    return process_payouts(payouts, predictor, aggregate=True)

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


def _empty_accuracy_scatter() -> List[go.Scatter]:
    return [go.Scatter(x=[], y=[], mode="lines", name="accuracy")]


def _empty_profit_scatter() -> List[go.Scatter]:
    return [go.Scatter(x=[], y=[], mode="lines", name="profit")]


def _empty_stakes_bar() -> List[go.Bar]:
    return [go.Bar(x=[], y=[], name="stakes", width=5)]


def _empty_trio() -> Tuple[go.Figure, go.Figure, go.Figure]:
    return _empty_accuracy_scatter(), _empty_profit_scatter(), _empty_stakes_bar()


def _make_figures(fig_tup: Tuple) -> Tuple[go.Figure, go.Figure, go.Figure]:
    accuracy_scatters, profit_scatters, stakes_scatters = fig_tup

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


@enforce_types
def get_figures(
    payouts: Optional[List], feeds: ArgFeeds, predictoors: List[str]
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
    if not payouts:
        return _make_figures(_empty_trio())

    accuracy_scatters, profit_scatters, stakes_scatters = [], [], []

    for predictor, feed in product(predictoors, feeds):
        slots, accuracies, profits, stakes = process_payouts(
            payouts, predictor, feed.contract
        )

        if not slots:
            continue

        short_name = f"{predictor[:5]} - {str(feed)}"
        accuracy_scatters.append(
            go.Scatter(x=slots, y=accuracies, mode="lines", name=short_name)
        )
        profit_scatters.append(
            go.Scatter(x=slots, y=profits, mode="lines", name=short_name)
        )
        stakes_scatters.append(go.Bar(x=slots, y=stakes, name=short_name, width=5))

    if not accuracy_scatters:
        accuracy_scatters = _empty_accuracy_scatter()

    if not profit_scatters:
        profit_scatters = _empty_profit_scatter()

    if not stakes_scatters:
        stakes_scatters = _empty_stakes_bar()

    return _make_figures((accuracy_scatters, profit_scatters, stakes_scatters))
