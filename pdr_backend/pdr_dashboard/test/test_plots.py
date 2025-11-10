import math
from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.pdr_dashboard.dash_components.plots import (
    create_figure,
    get_feed_figures,
    get_figures_and_metrics,
    process_payouts,
)
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def test_process_payouts(_sample_app):
    ## convert List[Payout] to List[dict]
    payouts = _sample_app.data.payouts_from_bronze_predictions(None, None)

    feed = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"
    user = "0x43584049fe6127ea6745d8ba42274e911f2a2d5c"

    ## filter payouts by user and feed
    filtered_payouts = payouts.filter(
        payouts["ID"].str.contains(user) & payouts["ID"].str.contains(feed)
    )
    filtered_payouts = filtered_payouts.sort("slot")
    tx_fee_cost = 0.2

    result = process_payouts(
        pf=filtered_payouts, tx_fee_cost=tx_fee_cost, calculate_confint=True
    )

    filtered_payouts = filtered_payouts.to_dicts()
    slots = result.slot_in_unixts
    accuracies = result.accuracies
    profits = result.profits
    stakes = result.stakes
    correct_predictions = result.correct_predictions
    predictions = result.predictions
    acc_u = result.acc_u.to_list()
    acc_l = result.acc_l.to_list()
    costs = result.tx_cost

    assert correct_predictions == 14
    assert costs > 0
    assert predictions == 24
    assert len(slots) == len(filtered_payouts)
    assert slots[0] == UnixTimeS(filtered_payouts[0]["slot"]).to_milliseconds()

    ## calculate accuracies
    test_accuracies = [
        (sum(p["payout"] > 0 for p in filtered_payouts[: i + 1]) / (i + 1)) * 100
        for i in range(len(filtered_payouts))
    ]

    assert len(accuracies) == len(test_accuracies)

    for i, accuracy in enumerate(accuracies):
        assert accuracy == test_accuracies[i]

    ## calculate profits
    test_profits = [
        sum(float(max(p["payout"], 0) - p["stake"]) for p in filtered_payouts[: i + 1])
        for i in range(len(filtered_payouts))
    ]

    assert len(profits) == len(test_profits)

    # check if profits are the same
    for i, profit in enumerate(profits):
        assert math.isclose(profit, test_profits[i], rel_tol=1e-9)

    test_stakes = [p["stake"] for p in filtered_payouts]

    assert len(stakes) == len(test_stakes)

    # check if stakes are the same
    for i, stake in enumerate(stakes):
        assert math.isclose(stake, test_stakes[i], rel_tol=1e-9)

    ## calculate accuracy intervals
    assert len(acc_u) == len(test_stakes)
    assert len(acc_l) == len(test_stakes)

    for acc_interval in acc_l:
        assert isinstance(acc_interval, float)

    for acc_interval in acc_u:
        assert isinstance(acc_interval, float)


class MockFigure:
    def __init__(self, data_traces):
        self.data_traces = data_traces
        self.layout = {}
        self.update_layout_called = 0

    def update_layout(self, **kwargs):
        self.layout.update(kwargs)
        self.update_layout_called += 1
        return self.layout


@enforce_types
@patch("plotly.graph_objects.Figure", new=MockFigure)
def test_create_figure():
    result = create_figure(
        data_traces=[],
        title="title",
        yaxis_title="yaxis_title",
        show_legend=True,
    )

    assert isinstance(result, MockFigure)
    assert result.data_traces == []
    assert result.layout == {
        "barmode": "stack",
        "title": "title",
        "margin": {"l": 20, "r": 0, "t": 50, "b": 0},
        "showlegend": True,
        "paper_bgcolor": "#f5f5f5",
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
        "yaxis": {"range": None, "title": "yaxis_title"},
        "xaxis": {
            "nticks": 5,
            "tickformat": "%m-%d %H:%M",
            "type": "date",
        },
    }

    assert result.update_layout_called == 1


@enforce_types
@patch("plotly.graph_objects.Figure", new=MockFigure)
def test_get_figures_and_metrics(_sample_app):
    db_mgr = _sample_app.data
    ## convert List[Payout] to List[dict]
    payouts = db_mgr.payouts_from_bronze_predictions(None, None)

    sample_feeds = ArgFeeds(
        [
            ArgFeed(
                contract="0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
                pair="ADA/USDT",
                exchange="binance",
                timeframe="1h",
            ),
        ]
    )
    sample_predictoors = ["0x43584049fe6127ea6745d8ba42274e911f2a2d5c"]
    fee_cost = 0.2

    figs_metrics = get_figures_and_metrics(
        payouts, sample_feeds, sample_predictoors, fee_cost
    )

    fig_accuracy = figs_metrics.fig_accuracy
    fig_profit = figs_metrics.fig_profit
    fig_costs = figs_metrics.fig_costs
    fig_stakes = figs_metrics.fig_stakes

    # Check if figures are instances of MockFigure
    assert isinstance(fig_accuracy, MockFigure)
    assert isinstance(fig_profit, MockFigure)
    assert isinstance(fig_costs, MockFigure)
    assert isinstance(fig_stakes, MockFigure)

    # Check if the figures have the correct layout and data traces
    assert len(fig_accuracy.data_traces) == 3
    assert len(fig_profit.data_traces) == 1
    assert len(fig_costs.data_traces) == 1
    assert len(fig_stakes.data_traces) == 1

    assert fig_accuracy.layout["title"] == "Accuracy"
    assert fig_profit.layout["title"] == "Profit"
    assert fig_costs.layout["title"] == "Costs"
    assert fig_stakes.layout["title"] == "Stakes"

    assert fig_accuracy.layout["yaxis"]["title"] == "Accuracy(%)"
    assert fig_profit.layout["yaxis"]["title"] == "Profit(USDC)"
    assert fig_costs.layout["yaxis"]["title"] == "Fees(USDC)"
    assert fig_stakes.layout["yaxis"]["title"] == "Stake(USDC)"

    assert fig_accuracy.update_layout_called == 1
    assert fig_profit.update_layout_called == 1
    assert fig_costs.update_layout_called == 1
    assert fig_stakes.update_layout_called == 1

    # Check metrics
    avg_accuracy = figs_metrics.avg_accuracy
    total_profit = figs_metrics.total_profit
    total_cost = figs_metrics.total_cost
    avg_stake = figs_metrics.avg_stake

    assert avg_accuracy is not None
    assert total_profit is not None
    assert total_cost is not None
    assert avg_stake is not None

    assert isinstance(avg_accuracy, float)
    assert isinstance(total_profit, float)
    assert isinstance(total_cost, float)
    assert isinstance(avg_stake, float)


def test_get_feed_figures(
    _sample_app,
):
    feed_id = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"
    db_mgr = _sample_app.data
    payouts = db_mgr.payouts_from_bronze_predictions([feed_id], None)

    subscriptions = db_mgr.feed_daily_subscriptions_by_feed_id(feed_id)

    # Execute the function
    figures = get_feed_figures(payouts, subscriptions)

    # Assertions to check if the figures have the expected data
    assert len(figures.sales_fig.data) == 1, "Sales figure should have one trace."
    assert len(figures.revenues_fig.data) == 1, "Revenues figure should have one trace."
    assert (
        len(figures.accuracies_fig.data) == 1
    ), "Accuracies figure should have one trace."
    assert len(figures.stakes_fig.data) == 1, "Stakes figure should have one trace."
    assert (
        len(figures.predictions_fig.data) == 1
    ), "Predictions figure should have one trace."
    assert len(figures.profits_fig.data) == 1, "Profits figure should have one trace."
