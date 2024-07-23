from itertools import product
from typing import List, Optional, Tuple, Union

import plotly.graph_objects as go
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def process_payouts(payouts: List[dict]) -> tuple:
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

    return (
        slot_in_date_format,
        accuracies,
        profits,
        stakes,
        correct_predictions,
        predictions,
    )


@enforce_types
def create_figure(
    data_traces: List[Union[go.Scatter, go.Bar]],
    title: str,
    yaxis_title: str,
    show_legend: bool = True,
    yaxis_range: Union[List, None] = None,
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
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        showlegend=show_legend,
        xaxis_nticks=4,
        bargap=0.1,
        barmode="stack",
        legend=legend_config,
        yaxis={"range": yaxis_range if yaxis_range else None, "title": yaxis_title},
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
        accuracy_scatters,
        title="Accuracy",
        yaxis_title="Accuracy(%)",
        yaxis_range=[30, 70],
    )

    fig_profit = create_figure(
        profit_scatters, title="Profit", yaxis_title="Profit(OCEAN)", show_legend=False
    )

    fig_costs = create_figure(
        stakes_scatters, title="Costs", yaxis_title="Stake(OCEAN)", show_legend=False
    )

    return fig_accuracy, fig_profit, fig_costs


@enforce_types
def get_figures_and_metrics(
    payouts: Optional[List], feeds: ArgFeeds, predictoors: List[str]
) -> Tuple[go.Figure, go.Figure, go.Figure, float | None, float | None, float | None]:
    """
    Get figures for accuracy, profit, and costs.
    Args:
        payouts (list): List of payouts data.
        feeds (list): List of feeds data.
        predictoors (list): List of predictoors data.
    Returns:
        tuple: Tuple of accuracy, profit, and costs figures, avg accuracy, total profit, avg stake
    """
    if not payouts:
        figures = _make_figures(_empty_trio())
        return figures[0], figures[1], figures[2], 0.0, 0.0, 0.0

    accuracy_scatters, profit_scatters, stakes_scatters = [], [], []
    avg_accuracy, total_profit, avg_stake = 0.0, 0.0, 0.0

    all_stakes = []
    prediction_count = 0
    correct_prediction_count = 0
    for predictor, feed in product(predictoors, feeds):
        # only filter for this particular predictoor and feed pair
        # in order to properly group the data
        filtered_payouts = [
            p for p in payouts if predictor in p["ID"] and feed.contract in p["ID"]
        ]

        slots, accuracies, profits, stakes, correct_predictions, predictions = (
            process_payouts(filtered_payouts)
        )

        if not slots:
            continue

        all_stakes.extend(stakes)
        prediction_count += predictions
        correct_prediction_count += correct_predictions

        total_profit = (profits[-1] + total_profit) if total_profit else profits[-1]

        short_name = f"{predictor[:5]} - {str(feed)}"
        accuracy_scatters.append(
            go.Scatter(x=slots, y=accuracies, mode="lines", name=short_name)
        )
        profit_scatters.append(
            go.Scatter(x=slots, y=profits, mode="lines", name=short_name)
        )
        stakes_scatters.append(go.Bar(x=slots, y=stakes, name=short_name, width=5))

    avg_stake = sum(all_stakes) / len(all_stakes) if all_stakes else 0.0
    avg_accuracy = (
        (correct_prediction_count / prediction_count) * 100 if prediction_count else 0.0
    )

    if not accuracy_scatters:
        accuracy_scatters = _empty_accuracy_scatter()

    if not profit_scatters:
        profit_scatters = _empty_profit_scatter()

    if not stakes_scatters:
        stakes_scatters = _empty_stakes_bar()

    figures = _make_figures((accuracy_scatters, profit_scatters, stakes_scatters))
    return (figures[0], figures[1], figures[2], avg_accuracy, total_profit, avg_stake)
