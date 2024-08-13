from itertools import product, groupby
from typing import List, Optional, Union, NamedTuple
from operator import itemgetter
import datetime

import plotly.graph_objects as go
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


class FeedModalFigures:
    def __init__(self):
        self.sales_fig: go.Figure = create_figure(
            [], "Sales", "Daily Sales (OCEAN)", False, ticker_format="%m-%d"
        )
        self.revenues_fig: go.Figure = create_figure(
            [], "Revenues", "Daily Revenues (OCEAN)", False, ticker_format="%m-%d"
        )
        self.accuracies_fig: go.Figure = create_figure(
            [], "Accuracy", "Avg Accuracy (OCEAN)", False, yaxis_range=[40, 70]
        )
        self.stakes_fig: go.Figure = create_figure([], "Stakes", "Stake (OCEAN)", False)
        self.predictions_fig: go.Figure = create_figure(
            [], "Predictions", "Predictions", False
        )
        self.profits_fig: go.Figure = create_figure(
            [], "Profits", "Pdr Profit (OCEAN)", False
        )


# pylint: disable=too-many-instance-attributes
class FiguresAndMetricsResult:
    def __init__(self):
        self.avg_accuracy = 0.0
        self.total_profit = 0.0
        self.avg_stake = 0.0
        self.total_cost = 0.0

        self.accuracy_scatters = []
        self.fig_accuracy = None

        self.profit_scatters = []
        self.fig_profit = None

        self.stakes_scatters = []
        self.fig_stakes = None

        self.costs_scatters = []
        self.fig_costs = None

    def make_figures(self):
        fig_config = {
            "accuracy_scatters": {
                "fallback": [go.Scatter(x=[], y=[], mode="lines", name="accuracy")],
                "fig_attr": "fig_accuracy",
                "args": {
                    "title": "Accuracy",
                    "yaxis_title": "Accuracy(%)",
                    "yaxis_range": [30, 70],
                },
            },
            "profit_scatters": {
                "fallback": [go.Scatter(x=[], y=[], mode="lines", name="profit")],
                "fig_attr": "fig_profit",
                "args": {
                    "title": "Profit",
                    "yaxis_title": "Profit(OCEAN)",
                    "show_legend": False,
                },
            },
            "costs_scatters": {
                "fallback": [go.Bar(x=[], y=[], name="costs")],
                "fig_attr": "fig_costs",
                "args": {
                    "title": "Costs",
                    "yaxis_title": "Fees(OCEAN)",
                    "show_legend": False,
                    "use_default_tick_format": True,
                },
            },
            "stakes_scatters": {
                "fallback": [go.Histogram(x=[], y=[], name="stakes")],
                "fig_attr": "fig_stakes",
                "args": {
                    "title": "Stakes",
                    "yaxis_title": "Stake(OCEAN)",
                    "show_legend": False,
                },
            },
        }

        for key, value in fig_config.items():
            scatters = getattr(self, key) or value["fallback"]

            fig = create_figure(
                scatters,
                **value["args"],
            )
            setattr(self, value["fig_attr"], fig)


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
        self.tx_cost = 0.0
        self.tx_costs = []

    def as_accuracy_scatters_bounds(self, short_name, show_confidence_interval: bool):
        scatters = [
            go.Scatter(
                x=self.slot_in_unixts,
                y=self.accuracies,
                mode="lines",
                name=short_name,
            )
        ]

        if show_confidence_interval:
            scatters = scatters + [
                go.Scatter(
                    x=self.slot_in_unixts,
                    y=[interval.acc_l * 100 for interval in self.acc_intervals],
                    mode="lines",
                    name="accuracy_lowerbound",
                    marker_color="#636EFA",
                    showlegend=False,
                ),
                go.Scatter(
                    x=self.slot_in_unixts,
                    y=[interval.acc_u * 100 for interval in self.acc_intervals],
                    mode="lines",
                    fill="tonexty",
                    name="accuracy_upperbound",
                    marker_color="#636EFA",
                    showlegend=False,
                ),
            ]

        return scatters

    def as_profit_scatters(self, short_name):
        return [
            go.Scatter(
                x=self.slot_in_unixts,
                y=self.profits,
                mode="lines",
                name=short_name,
            )
        ]

    def as_stakes_scatters(self, short_name):
        return [
            go.Histogram(
                x=self.slot_in_unixts,
                y=self.stakes,
                name=short_name,
            )
        ]

    def as_costs_scatters(self, label, short_name):
        return [
            go.Bar(
                x=[label],
                y=[self.tx_costs[-1]],
                name=short_name,
            )
        ]


def process_payouts(
    payouts: List[dict], tx_fee_cost, calculate_confint: bool = False
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
        processed.tx_cost += tx_fee_cost
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
        processed.tx_costs.append(processed.tx_cost)

    return processed


@enforce_types
def create_figure(
    data_traces: List[Union[go.Scatter, go.Bar]],
    title: str,
    yaxis_title: str,
    show_legend: bool = True,
    yaxis_range: Union[List, None] = None,
    use_default_tick_format: bool = False,
    ticker_format: Union[str, None] = None,
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
        xaxis=(
            {
                "type": "date",
                "nticks": 5,
                "tickformat": ticker_format if ticker_format else "%m-%d %H:%M",
            }
            if not use_default_tick_format
            else {"nticks": 4}
        ),
    )
    return fig


@enforce_types
def get_figures_and_metrics(
    payouts: Optional[List], feeds: ArgFeeds, predictors: List[str], fee_cost: float
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
    fee_cost = 2 * fee_cost

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
            payouts=filtered_payouts,
            tx_fee_cost=fee_cost,
            calculate_confint=show_confidence_interval,
        )

        all_stakes.extend(processed_data.stakes)
        correct_prediction_count += processed_data.correct_predictions
        prediction_count += processed_data.predictions
        figs_metrics.total_profit += (
            processed_data.profits[-1] if processed_data.profits else 0.0
        )
        figs_metrics.total_cost += (
            processed_data.tx_costs[-1] if processed_data.tx_costs else 0.0
        )

        short_name = f"{predictor[:5]} - {feed.output_for_legend()}"

        figs_metrics.accuracy_scatters.extend(
            processed_data.as_accuracy_scatters_bounds(
                short_name, show_confidence_interval
            )
        )

        figs_metrics.profit_scatters.extend(
            processed_data.as_profit_scatters(short_name)
        )

        figs_metrics.stakes_scatters.extend(
            processed_data.as_stakes_scatters(short_name)
        )

        figs_metrics.costs_scatters.extend(
            processed_data.as_costs_scatters(
                f"{feed.pair.base_str}-{feed.timeframe}-{predictor[:4]}", short_name
            )
        )

    figs_metrics.avg_stake = sum(all_stakes) / len(all_stakes) if all_stakes else 0.0
    figs_metrics.avg_accuracy = (
        (correct_prediction_count / prediction_count) * 100 if prediction_count else 0.0
    )
    figs_metrics.make_figures()

    return figs_metrics


@enforce_types
def get_feed_figures(payouts: Optional[List], subscriptions: List) -> FeedModalFigures:
    """
    Return figures for a selected feed from the feeds table.
    """

    # Initialize empty figures with default settings
    figures = FeedModalFigures()

    if not payouts or not subscriptions:
        return figures

    # Initialize lists for processing data
    slots, stakes, accuracies, profits, predictions_list = [], [], [], [], []
    subscription_purchases, subscription_revenues, subscription_dates = [], [], []

    # Process subscription data
    for subscription in subscriptions:
        subscription_purchases.append(subscription["count"])
        subscription_revenues.append(subscription["revenue"])
        unix_timestamp = int(
            datetime.datetime.combine(subscription["day"], datetime.time()).timestamp()
            * 1000
        )
        subscription_dates.append(unix_timestamp)

    # Sort payouts by slots and group by slot
    payouts.sort(key=itemgetter("slot"))
    grouped_payouts = {
        slot: list(group) for slot, group in groupby(payouts, key=itemgetter("slot"))
    }

    correct_predictions = 0
    total_predictions = 0

    # Process each slot's payouts
    for slot, payout_group in grouped_payouts.items():
        slot_stake = sum(p["stake"] for p in payout_group)
        slot_profit = sum(max(p["payout"], 0) - p["stake"] for p in payout_group)
        slot_predictions = len(payout_group)

        correct_predictions += sum(1 for p in payout_group if p["payout"] > 0)
        total_predictions += slot_predictions

        stakes.append(slot_stake)
        profits.append(slot_profit)
        accuracies.append((correct_predictions / total_predictions) * 100)
        slots.append(UnixTimeS(int(slot)).to_milliseconds())
        predictions_list.append(slot_predictions)

    # Update figures with the processed data
    figures.sales_fig.add_traces(go.Bar(x=subscription_dates, y=subscription_purchases))
    figures.revenues_fig.add_traces(
        go.Bar(x=subscription_dates, y=subscription_revenues)
    )
    figures.accuracies_fig.add_traces(
        go.Scatter(x=slots, y=accuracies, mode="lines", showlegend=False)
    )
    figures.stakes_fig.add_traces(
        go.Scatter(x=slots, y=stakes, mode="lines", showlegend=False)
    )
    figures.predictions_fig.add_traces(
        go.Scatter(x=slots, y=predictions_list, mode="lines", showlegend=False)
    )
    figures.profits_fig.add_traces(
        go.Scatter(x=slots, y=profits, mode="lines", showlegend=False)
    )

    return figures
