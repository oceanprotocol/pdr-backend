import plotly.graph_objects as go
import pandas as pd


def get_accuracy_chart(payouts, feeds, predictoors):
    slots = []
    accuracys = []
    scatters = []
    if payouts:
        for predictoor in predictoors:
            for feed in feeds:
                slots = []
                accuracys = []
                predictions = 0
                correct_predictions = 0
                for p in payouts:
                    if predictoor in p["ID"] and feed in p["ID"]:
                        predictions += 1
                        if p["payout"] > 0:
                            correct_predictions += 1

                        slots.append(p["slot"] / 1000)
                        accuracys.append((correct_predictions / predictions) * 100)
                if len(slots) > 0:
                    scatters.append(
                        go.Scatter(
                            x=slots,
                            y=accuracys,
                            mode="lines",
                            fill=None,
                            name=f"{predictoor[:5]} - {feed[:5]}",
                        ),
                    )
    else:
        scatters.append(
            go.Scatter(
                x=slots,
                y=accuracys,
                mode="lines",
                fill=None,
                name="accuracy upper bound",
            ),
        )
    fig = go.Figure()
    fig.add_traces(scatters)
    fig.update_layout(title="Accuracy")
    fig.update_layout(margin={"l": 20, "r": 0, "t": 50, "b": 0})
    return fig


def get_predictoors_stake_graph(predictoors_stake_data, feeds, predictoors):

    fig = go.Figure(
        layout=go.Layout(title="Cost", margin={"l": 20, "r": 0, "t": 50, "b": 0})
    )

    filtered_predictoors_stake_data = [
        stake
        for stake in predictoors_stake_data
        if any(
            predictoor == stake["user"]
            and feed["timeframe"] == stake["timeframe"]
            and feed["source"] == stake["source"]
            and feed["pair"] == stake["pair"]
            for predictoor in predictoors
            for feed in feeds
        )
    ]

    # check if filtered_predictoors_stake_data is empty
    if not filtered_predictoors_stake_data:
        return fig

    df = pd.DataFrame(filtered_predictoors_stake_data)

    users = df["user"].unique()
    for user in users:
        user_data = df[df["user"] == user]
        fig.add_trace(go.Bar(x=user_data["slot"], y=user_data["stake"], name=user[:5]))

    fig.update_layout(
        barmode="stack",
        bargap=0,
    )

    return fig
