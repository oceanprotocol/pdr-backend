import datetime
from abc import ABC, abstractmethod
from itertools import product
from typing import List, Union

import plotly.graph_objects as go
import polars as pl
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

        self.slots = pl.Series()
        self.stakes = pl.Series()
        self.accuracies = pl.Series()
        self.profits = pl.Series()
        self.predictions_list = pl.Series()

        self.subscription_purchases = pl.Series()
        self.subscription_revenues = pl.Series()
        self.subscription_dates = pl.Series()

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

        self.slots = pl.Series()
        self.stakes = pl.Series()
        self.accuracies = pl.Series()
        self.profits = pl.Series()
        self.incomes = pl.Series()
        self.nr_of_feeds = pl.Series()

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


class ProcessedPayouts:
    def __init__(self):
        self.slot_in_unixts = pl.Series()
        self.accuracies = pl.Series()
        self.profits = pl.Series()
        self.stakes = pl.Series()
        self.correct_predictions = 0
        self.predictions = 0
        self.acc_l = pl.Series()
        self.acc_u = pl.Series()
        self.tx_cost = 0.0
        self.tx_costs = pl.Series()

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
                    y=self.acc_l * 100,
                    mode="lines",
                    name="accuracy_lowerbound",
                    marker_color="#636EFA",
                    showlegend=False,
                ),
                go.Scatter(
                    x=self.slot_in_unixts,
                    y=self.acc_u * 100,
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
    pf: pl.DataFrame, tx_fee_cost, calculate_confint: bool = False
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
    processed.predictions = len(pf)

    pf = pf.with_columns(
        pl.lit(1).alias("predictions_crt"),
        (pl.col("payout").clip(lower_bound=0) - pl.col("stake")).alias("profit_change"),
        pl.when(pl.col("payout") > 0).then(1).otherwise(0).alias("correct_prediction"),
        pl.col("slot")
        .cast(pl.Int64)
        .map_elements(lambda x: UnixTimeS(x).to_milliseconds(), pl.Int64)
        .alias("slot_in_unixts"),
    )
    pf = pf.with_columns(
        pl.col("predictions_crt").cum_sum().alias("predictions_crt"),
        pl.col("correct_prediction").cum_sum().alias("correct_predictions_crt"),
    )
    processed.tx_cost = tx_fee_cost * len(pf)

    processed.correct_predictions = pf["correct_prediction"].sum()

    if calculate_confint:
        df = pf.with_columns(
            pl.struct(["correct_predictions_crt", "predictions_crt"])
            .map_elements(
                lambda x: proportion_confint(
                    count=x["correct_predictions_crt"], nobs=x["predictions_crt"]
                ),
                return_dtype=pl.List(pl.Float64),
            )
            .alias("acc_bounds"),
        )

        df = df.with_columns(
            [
                pl.col("acc_bounds").list.get(0).alias("acc_l"),
                pl.col("acc_bounds").list.get(1).alias("acc_u"),
            ]
        )

        processed.acc_l = df["acc_l"]
        processed.acc_u = df["acc_u"]

    pf = pf.with_columns(
        ((pl.col("correct_predictions_crt") / pl.col("predictions_crt")) * 100).alias(
            "accuracies"
        )
    )

    processed.slot_in_unixts = pf["slot_in_unixts"]
    processed.accuracies = pf["accuracies"]
    processed.profits = pf["profit_change"].cum_sum()
    processed.stakes = pf["stake"]
    processed.tx_costs = pl.Series([tx_fee_cost for i in range(len(pf))])

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
        paper_bgcolor="#f5f5f5",
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
    payouts: pl.DataFrame, feeds: ArgFeeds, predictors: List[str], fee_cost: float
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

    if payouts.is_empty():
        figs_metrics.make_figures()
        return figs_metrics

    all_stakes = []
    correct_prediction_count = 0
    prediction_count = 0

    for predictor, feed in product(predictors, feeds):
        filtered_payouts = payouts.filter(
            payouts["ID"].str.contains(predictor)
            & payouts["ID"].str.contains(str(feed.contract))
        )

        if filtered_payouts.is_empty():
            continue

        show_confidence_interval = len(predictors) == 1 and len(feeds) == 1

        processed_data = process_payouts(
            pf=filtered_payouts,
            tx_fee_cost=fee_cost,
            calculate_confint=show_confidence_interval,
        )

        all_stakes.extend(processed_data.stakes)
        correct_prediction_count += processed_data.correct_predictions
        prediction_count += processed_data.predictions

        figs_metrics.total_profit += (
            processed_data.profits[-1] if not processed_data.profits.is_empty() else 0.0
        )
        figs_metrics.total_cost += (
            processed_data.tx_costs[-1]
            if not processed_data.tx_costs.is_empty()
            else 0.0
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
    payouts: pl.DataFrame, subscriptions: pl.DataFrame
) -> FeedModalFigures:
    """
    Return figures for a selected feed from the feeds table.
    """
    # Initialize empty figures with default settings
    result = FeedModalFigures()

    if payouts.is_empty():
        return result

    # Process subscription data
    result.subscription_purchases = subscriptions["count"]
    result.subscription_revenues = subscriptions["revenue"]

    subscriptions = subscriptions.with_columns(
        pl.col("day")
        .map_elements(
            lambda x: datetime.datetime.combine(x, datetime.time()), pl.Datetime
        )
        .alias("day_dt"),
    )
    result.subscription_dates = subscriptions["day_dt"]

    payouts = payouts.with_columns(
        [
            (pl.col("payout").clip(lower_bound=0) - pl.col("stake")).alias("profit"),
            pl.when(pl.col("payout") > 0)
            .then(1)
            .otherwise(0)
            .alias("correct_prediction"),
            pl.lit(1).alias("count"),
        ]
    )

    payouts = payouts.with_columns(
        [
            pl.col("count").cum_sum().alias("cnt_cumsum"),
            pl.col("correct_prediction").cum_sum().alias("cnt_corrpred"),
        ]
    )

    sums = payouts.group_by("slot").sum().sort("slot")
    result.stakes = sums["stake"]
    result.profits = sums["profit"]

    sums = sums.with_columns(
        (pl.col("cnt_corrpred") / pl.col("cnt_cumsum") * 100).alias("accuracies"),
        pl.col("slot")
        .cast(pl.Int64)
        .map_elements(lambda x: UnixTimeS(x).to_milliseconds(), pl.Int64)
        .alias("slot_in_unixts"),
    )

    result.accuracies = sums["accuracies"]
    result.slots = sums["slot_in_unixts"]

    result.predictions_list = sums["count"]

    # Update figures with the processed data
    result.update_figures()

    return result


@enforce_types
def get_predictoor_figures(payouts: pl.DataFrame):
    """
    Return figures for a selected feed from the feeds table.
    """

    # Initialize empty figures with default settings
    result = PredictoorModalFigures()

    if payouts.is_empty():
        return result

    payouts = payouts.with_columns(
        (pl.col("payout").clip(lower_bound=0) - pl.col("stake")).alias("profit"),
        pl.lit(1).alias("count"),
        pl.when(pl.col("payout") > 0).then(1).otherwise(0).alias("correct_prediction"),
    )

    payouts = payouts.with_columns(
        pl.col("count").cum_sum().alias("cnt_cumsum"),
        pl.col("correct_prediction").cum_sum().alias("cnt_corrpred"),
    )

    sums = payouts.group_by("slot").sum().sort("slot")

    result.incomes = sums["payout"]
    result.stakes = sums["stake"]
    result.profits = sums["profit"].cum_sum()

    sums = sums.with_columns(
        (pl.col("cnt_corrpred") / pl.col("cnt_cumsum") * 100).alias("accuracies"),
        pl.col("slot")
        .cast(pl.Int64)
        .map_elements(lambda x: UnixTimeS(x).to_milliseconds(), pl.Int64)
        .alias("slot_in_unixts"),
    )

    result.accuracies = sums["accuracies"]
    result.slots = sums["slot_in_unixts"]

    result.nr_of_feeds = sums["count"]

    # Update figures with the processed data
    result.update_figures()

    return result
