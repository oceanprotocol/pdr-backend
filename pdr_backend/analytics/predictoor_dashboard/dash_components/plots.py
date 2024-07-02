import plotly.graph_objects as go
import pandas as pd


def get_figures(payouts, feeds, predictoors):
    slots = []
    accuracys = []
    profits = []
    accuracy_scatters = []
    profit_scatters = []
    if payouts:
        for predictoor in predictoors:
            for feed in feeds:
                slots = []
                profit = 0
                predictions = 0
                correct_predictions = 0
                for p in payouts:
                    if predictoor in p["ID"] and feed in p["ID"]:
                        predictions += 1
                        if p["payout"] > 0:
                            correct_predictions += 1
                            profit += p["payout"] - p["stake"]
                        else:
                            profit -= p["stake"]

                        slots.append(p["slot"] / 1000)
                        accuracys.append((correct_predictions / predictions) * 100)
                        profits.append(profit)
                if len(slots) > 0:
                    accuracy_scatters.append(
                        go.Scatter(
                            x=slots,
                            y=accuracys,
                            mode="lines",
                            fill=None,
                            name=f"{predictoor[:5]} - {feed[:5]}",
                        ),
                    )
                    profit_scatters.append(
                        go.Scatter(
                            x=slots,
                            y=profits,
                            mode="lines",
                            fill=None,
                            name=f"{predictoor[:5]} - {feed[:5]}",
                        ),
                    )
    else:
        accuracy_scatters.append(
            go.Scatter(
                x=slots,
                y=accuracys,
                mode="lines",
                fill=None,
                name="accuracy upper bound",
            ),
        )
        profit_scatters.append(
            go.Scatter(
                x=slots,
                y=profits,
                mode="lines",
                fill=None,
                name="accuracy upper bound",
            ),
        )
    fig_accuracy = go.Figure()
    fig_accuracy.add_traces(accuracy_scatters)
    fig_accuracy.update_layout(title="Accuracy")
    fig_accuracy.update_layout(margin={"l": 20, "r": 0, "t": 50, "b": 0})

    fig_profit = go.Figure()
    fig_profit.add_traces(profit_scatters)
    fig_profit.update_layout(title="Profit")
    fig_profit.update_layout(margin={"l": 20, "r": 0, "t": 50, "b": 0})
    return fig_accuracy, fig_profit


def get_predictoors_stake_graph(payouts_data, feeds, predictoors):

    fig = go.Figure(
        layout=go.Layout(title="Cost", margin={"l": 20, "r": 0, "t": 50, "b": 0})
    )

    filtered_payots_data = []
    for p in payouts_data:
        for feed in feeds:
            for predictoor in predictoors:
                if feed in p["ID"] and predictoor in p["ID"]:
                    filtered_payots_data.append(p)

    # check if filtered_predictoors_stake_data is empty
    if not filtered_payots_data:
        return fig

    df = pd.DataFrame(filtered_payots_data)

    users = df["user"].unique()
    for user in users:
        user_data = df[df["user"] == user]
        user_data["slot"] = user_data["slot"] / 1000
        fig.add_trace(go.Bar(x=user_data["slot"], y=user_data["stake"], name=user[:5]))

    fig.update_layout(
        barmode="stack",
        bargap=0,
        xaxis_title="Slot",
        yaxis_title="Stake (OCEAN)",
    )

    return fig
