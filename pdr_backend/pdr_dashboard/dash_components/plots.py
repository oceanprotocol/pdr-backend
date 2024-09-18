import datetime
from abc import ABC, abstractmethod
from itertools import product
from typing import List, NamedTuple, Union

import pandas
import plotly.graph_objects as go
from enforce_typing import enforce_types
from statsmodels.stats.proportion import proportion_confint

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.util.time_types import UnixTimeS


class ModalFigures(ABC):

    @abstractmethod
    def get_figures(self):
        pass

    @abstractmethod
    def update_figures(self):
        pass


# pylint: disable=too-many-instance-attributes
class FeedModalFigures(ModalFigures):
    def __init__(self):
        fig_config = {
            "sales_fig": {
                "title": "Sales",
                "yaxis_title": "Daily Sales (OCEAN)",
                "show_legend": False,
                "ticker_format": "%m-%d",
            },
            "revenues_fig": {
                "title": "Revenues",
                "yaxis_title": "Daily Revenues (OCEAN)",
                "show_legend": False,
                "ticker_format": "%m-%d",
            },
            "accuracies_fig": {
                "title": "Accuracy",
                "yaxis_title": "Avg Accuracy (OCEAN)",
                "show_legend": False,
                "yaxis_range": [40, 70],
            },
            "stakes_fig": {
                "title": "Stakes",
                "yaxis_title": "Stake (OCEAN)",
                "show_legend": False,
            },
            "predictions_fig": {
                "title": "Predictions",
                "yaxis_title": "Predictions",
                "show_legend": False,
            },
            "profits_fig": {
                "title": "Profits",
                "yaxis_title": "Pdr Profit (OCEAN)",
                "show_legend": False,
            },
        }

        for key, value in fig_config.items():
            setattr(self, key, create_figure([], **value))

        self.slots = []
        self.stakes = []
        self.accuracies = []
        self.profits = []
        self.predictions_list = []

        self.subscription_purchases = []
        self.subscription_revenues = []
        self.subscription_dates = []

    def update_figures(self):
        self.sales_fig.add_traces(
            go.Bar(x=self.subscription_dates, y=self.subscription_purchases)
        )

        defaults = {
            "mode": "lines",
            "showlegend": False,
        }

        self.revenues_fig.add_traces(
            go.Bar(x=self.subscription_dates, y=self.subscription_revenues)
        )
        self.accuracies_fig.add_traces(
            go.Scatter(x=self.slots, y=self.accuracies, **defaults)
        )
        self.stakes_fig.add_traces(go.Scatter(x=self.slots, y=self.stakes, **defaults))
        self.predictions_fig.add_traces(
            go.Scatter(x=self.slots, y=self.predictions_list, **defaults)
        )
        self.profits_fig.add_traces(
            go.Scatter(x=self.slots, y=self.profits, **defaults)
        )

    def get_figures(self):
        return [
            self.sales_fig,
            self.revenues_fig,
            self.accuracies_fig,
            self.stakes_fig,
            self.predictions_fig,
            self.profits_fig,
        ]


# pylint: disable=too-many-instance-attributes
class PredictoorModalFigures(ModalFigures):
    def __init__(self):
        fig_config = {
            "incomes_fig": {
                "title": "Incomes",
                "yaxis_title": "Gross Income (OCEAN)",
                "show_legend": False,
                "ticker_format": "%m-%d",
            },
            "accuracies_fig": {
                "title": "Accuracy",
                "yaxis_title": "Avg Accuracy (OCEAN)",
                "show_legend": False,
                "yaxis_range": [40, 70],
            },
            "stakes_fig": {
                "title": "Stakes",
                "yaxis_title": "Stake (OCEAN)",
                "show_legend": False,
            },
            "profits_fig": {
                "title": "Total Profit over time",
                "yaxis_title": "Profit (OCEAN)",
                "show_legend": False,
            },
            "nr_of_feeds_fig": {
                "title": "Nr. of Feeds",
                "yaxis_title": "Feeds",
                "show_legend": False,
            },
        }

        for key, value in fig_config.items():
            setattr(self, key, create_figure([], **value))

        self.slots = []
        self.stakes = []
        self.accuracies = []
        self.profits = []
        self.incomes = []
        self.nr_of_feeds = []

    def update_figures(self):
        defaults = {
            "mode": "lines",
            "showlegend": False,
        }

        self.incomes_fig.add_traces(
            go.Bar(x=self.slots, y=self.incomes, showlegend=False)
        )
        self.accuracies_fig.add_traces(
            go.Scatter(x=self.slots, y=self.accuracies, **defaults)
        )
        self.stakes_fig.add_traces(
            go.Bar(x=self.slots, y=self.stakes, showlegend=False)
        )
        self.profits_fig.add_traces(
            go.Scatter(x=self.slots, y=self.profits, **defaults)
        )
        self.nr_of_feeds_fig.add_traces(
            go.Bar(x=self.slots, y=self.nr_of_feeds, showlegend=False)
        )

    def get_figures(self):
        return [
            self.incomes_fig,
            self.accuracies_fig,
            self.stakes_fig,
            self.profits_fig,
            self.nr_of_feeds_fig,
        ]


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
    payouts: pandas.DataFrame, tx_fee_cost, calculate_confint: bool = False
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

    p = payouts.copy()
    processed.predictions = len(payouts)
    p["predictions_crt"] = range(1, len(payouts) + 1)
    processed.tx_cost = tx_fee_cost * len(payouts)
    p["profit_change"] = p.apply(
        lambda x: max(x["payout"], 0) - x["stake"], axis=1
    ).astype(float)
    p["correct_prediction"] = p["payout"].apply(lambda x: x > 0).astype(int)
    p["correct_predictions_crt"] = p["correct_prediction"].cumsum()
    processed.correct_predictions = p["correct_prediction"].sum()

    if calculate_confint:
        series = p.apply(
            lambda x: proportion_confint(
                count=x["correct_predictions_crt"], nobs=x["predictions_crt"]
            ),
            axis=1,
        ).apply(pandas.Series)

        p["acc_l"] = series[0]
        p["acc_u"] = series[1]

    processed.acc_intervals = p.apply(
        lambda x: AccInterval(x["acc_l"], x["acc_u"]), axis=1
    ).tolist()

    processed.slot_in_unixts = (
        p["slot"].apply(lambda x: UnixTimeS(int(x)).to_milliseconds()).tolist()
    )
    processed.accuracies = p.apply(
        lambda x: x["correct_predictions_crt"] / x["predictions_crt"] * 100, axis=1
    ).tolist()

    processed.profits = p["profit_change"].cumsum().tolist()
    processed.stakes = p["stake"].tolist()
    processed.tx_costs = [processed.tx_cost] * len(payouts)

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
    payouts: pandas.DataFrame, feeds: ArgFeeds, predictors: List[str], fee_cost: float
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

    if payouts.empty:
        figs_metrics.make_figures()
        return figs_metrics

    all_stakes = []
    correct_prediction_count = 0
    prediction_count = 0

    for predictor, feed in product(predictors, feeds):
        filtered_payouts = payouts[
            payouts["ID"].str.contains(predictor)
            & payouts["ID"].str.contains(feed.contract)
        ]

        if filtered_payouts.empty:
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

        short_name = f"{predictor[:5]} - {feed.str_without_exchange()}"

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
def get_feed_figures(
    payouts: pandas.DataFrame, subscriptions: pandas.DataFrame
) -> FeedModalFigures:
    """
    Return figures for a selected feed from the feeds table.
    """
    # Initialize empty figures with default settings
    result = FeedModalFigures()

    if payouts.empty:
        return result

    # Process subscription data
    result.subscription_purchases = subscriptions["count"].tolist()
    result.subscription_revenues = subscriptions["revenue"].tolist()
    result.subscription_dates = (
        subscriptions["day"]
        .apply(lambda x: datetime.datetime.combine(x, datetime.time()))
        .tolist()
    )

    payouts["profit"] = payouts.apply(
        lambda x: max(x["payout"], 0) - x["stake"], axis=1
    )
    payouts["correct_prediction"] = payouts["payout"].apply(lambda x: x > 0).astype(int)
    payouts["count"] = 1

    sums = payouts.groupby("slot").sum()
    result.stakes = sums["stake"].tolist()
    result.profits = sums["profit"]
    result.accuracies = sums.apply(
        lambda x: x["correct_prediction"] / x["count"] * 100, axis=1
    )
    result.slots = [
        UnixTimeS(int(slot)).to_milliseconds() for slot in sums.index.tolist()
    ]
    result.predictions_list = sums["count"].tolist()

    # Update figures with the processed data
    result.update_figures()

    return result


@enforce_types
def get_predictoor_figures(payouts: pandas.DataFrame):
    """
    Return figures for a selected feed from the feeds table.
    """

    # Initialize empty figures with default settings
    result = PredictoorModalFigures()

    if payouts.empty:
        return result

    payouts["profit"] = payouts.apply(
        lambda x: max(x["payout"], 0) - x["stake"], axis=1
    )
    payouts["correct_prediction"] = payouts["payout"].apply(lambda x: x > 0).astype(int)
    payouts["count"] = 1

    sums = payouts.groupby("slot").sum()

    result.incomes = sums["payout"].tolist()
    result.stakes = sums["stake"].tolist()
    result.profits = sums["profit"].cumsum().tolist()
    result.accuracies = sums.apply(
        lambda x: x["correct_prediction"] / x["count"] * 100, axis=1
    )
    result.slots = [
        UnixTimeS(int(slot)).to_milliseconds() for slot in sums.index.tolist()
    ]
    result.nr_of_feeds = sums["count"].tolist()

    # Update figures with the processed data
    result.update_figures()

    return result
