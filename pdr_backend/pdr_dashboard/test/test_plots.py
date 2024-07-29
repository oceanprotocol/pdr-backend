from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.pdr_dashboard.dash_components.plots import (
    process_payouts,
    create_figure,
    get_figures_and_metrics,
)
from pdr_backend.util.time_types import UnixTimeS
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


@enforce_types
def test_process_payouts(
    _sample_payouts,
):
    ## convert List[Payout] to List[dict]
    payouts = [p.__dict__ for p in _sample_payouts]

    user = "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"
    feed = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"

    ## filter payouts by user and feed
    filtered_payouts = [p for p in payouts if user in p["ID"] and feed in p["ID"]]
    filtered_payouts = sorted(filtered_payouts, key=lambda x: x["slot"])
    tx_fee_cost = 0.2

    result = process_payouts(
        payouts=filtered_payouts, tx_fee_cost=tx_fee_cost, calculate_confint=True
    )

    slots = result.slot_in_unixts
    accuracies = result.accuracies
    profits = result.profits
    stakes = result.stakes
    correct_predictions = result.correct_predictions
    predictions = result.predictions
    acc_intervals = result.acc_intervals
    costs = result.tx_cost

    assert correct_predictions == 0
    assert costs > 0
    assert predictions == 2
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
        sum(
            (p["payout"] - p["stake"]) if p["payout"] > 0 else -p["stake"]
            for p in filtered_payouts[: i + 1]
        )
        for i in range(len(filtered_payouts))
    ]

    assert len(profits) == len(test_profits)

    # check if profits are the same
    for i, profit in enumerate(profits):
        assert profit == test_profits[i]

    test_stakes = [p["stake"] for p in filtered_payouts]

    assert len(stakes) == len(test_stakes)

    # check if stakes are the same
    for i, stake in enumerate(stakes):
        assert stake == test_stakes[i]

    assert len(acc_intervals) == len(test_stakes)

    for i, acc_interval in enumerate(acc_intervals):
        assert isinstance(acc_interval.acc_l, float)
        assert isinstance(acc_interval.acc_u, float)


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
def test_get_figures_and_metrics(
    _sample_payouts,
):
    ## convert List[Payout] to List[dict]
    payouts = [p.__dict__ for p in _sample_payouts]
    sample_feeds = ArgFeeds(
        [
            ArgFeed(
                contract="b0x18f54cc21b7a2fdd011bea06bba7801b280e315",
                pair="BTC/USDT",
                exchange="binance",
                timeframe="1h",
            ),
        ]
    )
    sample_predictoors = ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"]
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
    assert len(fig_accuracy.data_traces) == 1
    assert len(fig_profit.data_traces) == 1
    assert len(fig_costs.data_traces) == 1
    assert len(fig_stakes.data_traces) == 1

    assert fig_accuracy.layout["title"] == "Accuracy"
    assert fig_profit.layout["title"] == "Profit"
    assert fig_costs.layout["title"] == "Costs"
    assert fig_stakes.layout["title"] == "Stakes"

    assert fig_accuracy.layout["yaxis"]["title"] == "Accuracy(%)"
    assert fig_profit.layout["yaxis"]["title"] == "Profit(OCEAN)"
    assert fig_costs.layout["yaxis"]["title"] == "Fees(OCEAN)"
    assert fig_stakes.layout["yaxis"]["title"] == "Stake(OCEAN)"

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
