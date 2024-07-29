from itertools import product
from typing import List, Optional, Union, NamedTuple

import plotly.graph_objects as go
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


# pylint: disable=too-many-instance-attributes
class FiguresAndMetricsResult:
    def __init__(self):
        self.avg_accuracy = 0.0
        self.total_profit = 0.0
        self.avg_stake = 0.0

        self.accuracy_scatters = []
        self.fig_accuracy = None

        self.profit_scatters = []
        self.fig_profit = None

        self.stakes_scatters = []
        self.fig_costs = None

    def make_figures(self):
        accuracy_scatters = (
            self.accuracy_scatters
            if self.accuracy_scatters
            else [go.Scatter(x=[], y=[], mode="lines", name="accuracy")]
        )

        self.fig_accuracy = create_figure(
            accuracy_scatters,
            title="Accuracy",
            yaxis_title="Accuracy(%)",
            yaxis_range=[30, 70],
        )

        profit_scatters = (
            self.profit_scatters
            if self.profit_scatters
            else [go.Scatter(x=[], y=[], mode="lines", name="profit")]
        )
        self.fig_profit = create_figure(
            profit_scatters,
            title="Profit",
            yaxis_title="Profit(OCEAN)",
            show_legend=False,
        )

        stakes_scatters = (
            self.stakes_scatters
            if self.stakes_scatters
            else [go.Bar(x=[], y=[], name="stakes", width=5)]
        )
        self.fig_costs = create_figure(
            stakes_scatters,
            title="Costs",
            yaxis_title="Stake(OCEAN)",
            show_legend=False,
        )


class AccInterval(NamedTuple):
    acc_l: float
    acc_u: float


class ProcessedPayouts:
    def __init__(self):
        self.slot_in_unixts = []
        self.accuracies = []
        self.profits = []
        self.stakes = []
        self.correct_predictions = 0
        self.predictions = 0
        self.acc_intervals = []


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

    processed = ProcessedPayouts()

    profit = 0.0
    for p in payouts:
        processed.predictions += 1
        profit_change = float(max(p["payout"], 0) - p["stake"])
        profit += profit_change
        processed.correct_predictions += p["payout"] > 0

        if calculate_confint:
            acc_l, acc_u = proportion_confint(
                count=processed.correct_predictions, nobs=processed.predictions
            )

            processed.acc_intervals.append(
                AccInterval(
                    acc_l,
                    acc_u,
                )
            )

        processed.slot_in_unixts.append(UnixTimeS(int(p["slot"])).to_milliseconds())
        processed.accuracies.append(
            (processed.correct_predictions / processed.predictions) * 100
        )
        processed.profits.append(profit)
        processed.stakes.append(p["stake"])

    return processed


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
        yaxis_range (list, optional): Custom range for the y-axis.
        xaxis_tickformat (str, optional): Custom format string for x-axis ticks.
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
        legend=legend_config,
        barmode="stack",
        yaxis={"range": yaxis_range if yaxis_range else None, "title": yaxis_title},
        xaxis={
            "type": "date",
            "nticks": 5,
            "tickformat": "%m-%d %H:%M",
        },
    )
    return fig


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
    figs_metrics = FiguresAndMetricsResult()

    if not payouts:
        figs_metrics.make_figures()
        return figs_metrics

    all_stakes = []
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
        figs_metrics.total_profit += (
            processed_data.profits[-1] if processed_data.profits else 0.0
        )

        short_name = f"{predictor[:5]} - {str(feed)}"

        if show_confidence_interval:
            figs_metrics.accuracy_scatters.append(
                go.Scatter(
                    x=processed_data.slot_in_unixts,
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
            figs_metrics.accuracy_scatters.append(
                go.Scatter(
                    x=processed_data.slot_in_unixts,
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

        figs_metrics.accuracy_scatters.append(
            go.Scatter(
                x=processed_data.slot_in_unixts,
                y=processed_data.accuracies,
                mode="lines",
                name=short_name,
            )
        )
        figs_metrics.profit_scatters.append(
            go.Scatter(
                x=processed_data.slot_in_unixts,
                y=processed_data.profits,
                mode="lines",
                name=short_name,
            )
        )
        figs_metrics.stakes_scatters.append(
            go.Histogram(
                x=processed_data.slot_in_unixts,
                y=processed_data.stakes,
                name=short_name,
            )
        )

    figs_metrics.avg_stake = sum(all_stakes) / len(all_stakes) if all_stakes else 0.0
    figs_metrics.avg_accuracy = (
        (correct_prediction_count / prediction_count) * 100 if prediction_count else 0.0
    )
    figs_metrics.make_figures()

    return figs_metrics
