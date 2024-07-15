from unittest.mock import patch

from enforce_typing import enforce_types

from pdr_backend.predictoor_dashboard.dash_components.plots import (
    process_payouts,
    create_figure,
    get_figures,
)
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def test_process_payouts(
    _sample_payouts,
):
    ## convert List[Payout] to List[dict]
    payouts = [p.__dict__ for p in _sample_payouts]

    user = "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"
    feed = "0x18f54cc21b7a2fdd011bea06bba7801b280e3151"
    result = process_payouts(payouts, user, feed)

    ## filter payouts by user and feed
    filtered_payouts = [p for p in payouts if user in p["ID"] and feed in p["ID"]]
    filtered_payouts = sorted(filtered_payouts, key=lambda x: x["slot"])

    assert len(result) == 4

    slots, accuracies, profits, stakes = result

    assert len(slots) == len(filtered_payouts)
    assert slots[0] == UnixTimeS(
        filtered_payouts[0]["slot"]
    ).to_milliseconds().to_dt().strftime("%m-%d %H:%M")

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
        "bargap": 0.1,
        "barmode": "stack",
        "title": "title",
        "yaxis_title": "yaxis_title",
        "margin": {"l": 20, "r": 0, "t": 50, "b": 0},
        "showlegend": True,
        "xaxis_nticks": 4,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    }

    assert result.update_layout_called == 1


@enforce_types
@patch("plotly.graph_objects.Figure", new=MockFigure)
def test_get_figures(
    _sample_payouts,
):
    ## convert List[Payout] to List[dict]
    payouts = [p.__dict__ for p in _sample_payouts]
    sample_feeds = [
        {"contract": "0x18f54cc21b7a2fdd011bea06bba7801b280e3151", "feed_name": "Feed1"}
    ]
    sample_predictoors = ["0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"]

    fig_accuracy, fig_profit, fig_costs = get_figures(
        payouts, sample_feeds, sample_predictoors
    )

    # Check if figures are instances of MockFigure
    assert isinstance(fig_accuracy, MockFigure)
    assert isinstance(fig_profit, MockFigure)
    assert isinstance(fig_costs, MockFigure)

    # Check if the figures have the correct layout and data traces
    assert len(fig_accuracy.data_traces) == 1
    assert len(fig_profit.data_traces) == 1
    assert len(fig_costs.data_traces) == 1

    assert fig_accuracy.layout["title"] == "Accuracy"
    assert fig_profit.layout["title"] == "Profit"
    assert fig_costs.layout["title"] == "Costs"

    assert fig_accuracy.layout["yaxis_title"] == "'%' accuracy over time"
    assert fig_profit.layout["yaxis_title"] == "OCEAN profit over time"
    assert fig_costs.layout["yaxis_title"] == "Stake (OCEAN) at a time"

    assert fig_accuracy.update_layout_called == 1
    assert fig_profit.update_layout_called == 1
    assert fig_costs.update_layout_called == 1
