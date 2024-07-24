from itertools import product
from typing import List, Optional, Tuple, Union, NamedTuple

import plotly.graph_objects as go
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


class FiguresAndMetricsResult(NamedTuple):
    accuracy_figure: go.Figure
    profit_figure: go.Figure
    costs_figure: go.Figure
    avg_accuracy: Optional[float]
    total_profit: Optional[float]
    avg_stake: Optional[float]


class AccInterval(NamedTuple):
    acc_l: float
    acc_u: float


class ProcessedPayouts(NamedTuple):
    slot_in_date_format: List[str]
    accuracies: List[float]
    profits: List[float]
    stakes: List[float]
    correct_predictions: int
    predictions: int
    acc_intervals: List[AccInterval]


@enforce_types
def process_payouts(
    payouts: List[dict], calculate_confint: bool = False
) -> ProcessedPayouts:
    """
    Process payouts data for a given predictor and feed.
    Args:
        payouts (list): List of payouts data.
        predictor (str): Predictor address.
        feed (str): Feed contract address.
    Returns:
        tuple: Tuple of slots, accuracies, profits, stakes.
    """
    (
        _,
        accuracies,
        profits,
        stakes,
        correct_predictions,
        predictions,
        acc_intervals,
    ) = ProcessedPayouts([], [], [], [], 0, 0, [])

    profit = 0.0
    slots = []
    for p in payouts:
        predictions += 1
        profit_change = float(max(p["payout"], 0) - p["stake"])
        profit += profit_change
        correct_predictions += p["payout"] > 0

        if calculate_confint:
            acc_l, acc_u = proportion_confint(
                count=correct_predictions, nobs=predictions
            )

            acc_intervals.append(
                AccInterval(
                    acc_l,
                    acc_u,
                )
            )

        slots.append(p["slot"])
        accuracies.append((correct_predictions / predictions) * 100)
        profits.append(profit)
        stakes.append(p["stake"])

    slot_in_date_format = [
        UnixTimeS(ts).to_milliseconds().to_dt().strftime("%m-%d %H:%M") for ts in slots
    ]

    return ProcessedPayouts(
        slot_in_date_format,
        accuracies,
        profits,
        stakes,
        correct_predictions,
        predictions,
        acc_intervals,
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
    payouts: Optional[List], feeds: ArgFeeds, predictors: List[str]
) -> FiguresAndMetricsResult:
    """
    Get figures for accuracy, profit, and costs.
    Args:
        payouts (list): List of payouts data.
        feeds (list): List of feeds data.
        predictors (list): List of predictors data.
    Returns:
        FiguresAndMetricsResult: Tuple of accuracy, profit, and
        costs figures, avg accuracy, total profit, avg stake
    """
    if not payouts:
        accuracy_fig, profit_fig, costs_fig = _make_figures(_empty_trio())
        return FiguresAndMetricsResult(
            accuracy_fig, profit_fig, costs_fig, 0.0, 0.0, 0.0
        )

    accuracy_scatters, profit_scatters, stakes_scatters = [], [], []
    all_stakes = []
    total_profit = 0.0
    correct_prediction_count = 0
    prediction_count = 0

    for predictor, feed in product(predictors, feeds):
        filtered_payouts = [
            p for p in payouts if predictor in p["ID"] and feed.contract in p["ID"]
        ]

        if not filtered_payouts:
            continue

        show_confidence_interval = len(predictors) == 1 and len(feeds) == 1

        processed_data = process_payouts(
            payouts=filtered_payouts, calculate_confint=show_confidence_interval
        )

        all_stakes.extend(processed_data.stakes)
        correct_prediction_count += processed_data.correct_predictions
        prediction_count += processed_data.predictions
        total_profit += processed_data.profits[-1] if processed_data.profits else 0.0

        short_name = f"{predictor[:5]} - {str(feed)}"

        if show_confidence_interval:
            accuracy_scatters.append(
                go.Scatter(
                    x=processed_data.slot_in_date_format,
                    y=[
                        interval.acc_l * 100
                        for interval in processed_data.acc_intervals
                    ],
                    mode="lines",
                    name="accuracy_lowerbound",
                    marker_color="#636EFA",
                    showlegend=False,
                )
            )
            accuracy_scatters.append(
                go.Scatter(
                    x=processed_data.slot_in_date_format,
                    y=[
                        interval.acc_u * 100
                        for interval in processed_data.acc_intervals
                    ],
                    mode="lines",
                    fill="tonexty",
                    name="accuracy_upperbound",
                    marker_color="#636EFA",
                    showlegend=False,
                )
            )

        accuracy_scatters.append(
            go.Scatter(
                x=processed_data.slot_in_date_format,
                y=processed_data.accuracies,
                mode="lines",
                name=short_name,
            )
        )
        profit_scatters.append(
            go.Scatter(
                x=processed_data.slot_in_date_format,
                y=processed_data.profits,
                mode="lines",
                name=short_name,
            )
        )
        stakes_scatters.append(
            go.Bar(
                x=processed_data.slot_in_date_format,
                y=processed_data.stakes,
                name=short_name,
                width=5,
            )
        )

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

    accuracy_fig, profit_fig, costs_fig = _make_figures(
        (accuracy_scatters, profit_scatters, stakes_scatters)
    )

    return FiguresAndMetricsResult(
        accuracy_fig, profit_fig, costs_fig, avg_accuracy, total_profit, avg_stake
    )
