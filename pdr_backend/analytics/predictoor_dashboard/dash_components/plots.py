import plotly.graph_objects as go


def create_scatter(name, x_data, y_data, mode="lines"):
    return go.Scatter(x=x_data, y=y_data, mode=mode, name=name)


def create_bar(name, x_data, y_data):
    return go.Bar(x=x_data, y=y_data, name=name)


def process_payouts(payouts, predictor, feed):
    slots = []
    accuracies = []
    profits = []
    stakes = []
    profit = 0
    predictions = 0
    correct_predictions = 0
    for p in payouts:
        if predictor in p["ID"] and feed in p["ID"]:
            predictions += 1
            if p["payout"] > 0:
                correct_predictions += 1
                profit += p["payout"] - p["stake"]
            else:
                profit -= p["stake"]

            stakes.append(p["stake"])
            slots.append(p["slot"] / 1000)
            accuracies.append((correct_predictions / predictions) * 100)
            profits.append(profit)
    return slots, accuracies, profits, stakes


def get_figures(payouts, feeds, predictoors):
    accuracy_scatters = []
    profit_scatters = []
    stakes_scatters = []

    if payouts:
        for predictor in predictoors:
            for feed in feeds:
                slots, accuracies, profits, stakes = process_payouts(
                    payouts, predictor, feed["contract"]
                )
                if slots:
                    short_name = f"{predictor[:5]} - {feed['feed_name']}"
                    accuracy_scatters.append(
                        create_scatter(short_name, slots, accuracies)
                    )
                    profit_scatters.append(create_scatter(short_name, slots, profits))
                    stakes_scatters.append(create_bar(short_name, slots, stakes))
    else:
        accuracy_scatters.append(create_scatter("accuracy", [], []))
        profit_scatters.append(create_scatter("profit", [], []))
        stakes_scatters.append(create_bar("stakes", [], []))

    fig_accuracy = go.Figure(accuracy_scatters)
    fig_accuracy.update_layout(
        title="Accuracy",
        yaxis_title="'%' accuracy over time",
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        legend={
            "orientation": "h",  # Horizontal orientation
            "yanchor": "bottom",  # Anchor the legend to the bottom
            "y": 1.02,  # Position the legend slightly above the plot
            "xanchor": "right",  # Anchor the legend to the right
            "x": 1,  # Position the legend to the right
        },
    )

    fig_profit = go.Figure(profit_scatters)
    fig_profit.update_layout(
        title="Profit",
        yaxis_title="OCEAN profit over time",
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        showlegend=False,
    )

    fig_costs = go.Figure(stakes_scatters)
    fig_costs.update_layout(
        title="Costs",
        yaxis_title="Stake (OCEAN) at a time",
        margin={"l": 20, "r": 0, "t": 50, "b": 0},
        showlegend=False,
    )

    return fig_accuracy, fig_profit, fig_costs
