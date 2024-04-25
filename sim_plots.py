import os
from pathlib import Path

import plotly
from dash import Dash, Input, Output, State, callback, dcc, html

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.sim_plotter import SimPlotter

# TODO: run with specific state -> check args in Readme
# TODO: run with specific ports for multiple instances -> check args in Readme
# TODO: display slider to select state and add callback
# TODO: handle clickdata in varimps callback


app = Dash(__name__)
app.config["suppress_callback_exceptions"] = True

sim_plotter = SimPlotter()
canvas = [
    "pdr_profit_vs_time",
    "trader_profit_vs_time",
    "accuracy_vs_time",
    "pdr_profit_vs_ptrue",
    "trader_profit_vs_ptrue",
    "aimodel_varimps",
    "aimodel_response",
    "f1_precision_recall_vs_time",
]
empty_graphs_template = [
    dcc.Graph(figure=plotly.graph_objs.Figure(), id=key) for key in canvas
]


app.layout = html.Div(
    html.Div(
        [
            html.Div(empty_graphs_template, id="live-graphs"),
            dcc.Interval(
                id="interval-component",
                interval=3 * 1000,  # in milliseconds
                n_intervals=0,
                disabled=False,
            ),
        ]
    )
)


@app.callback(
    Output("interval-component", "disabled"),
    [Input("sim_current_ts", "className")],
    [State("interval-component", "disabled")],
)
# pylint: disable=unused-argument
def callback_func_start_stop_interval(value, disabled_state):
    # stop refreshing if final state was reached
    return value == "finalState"


def get_latest_state_id():
    path = sorted(Path("sim_state").iterdir(), key=os.path.getmtime)[-1]
    return str(path).replace("sim_state/", "")


def get_figures_by_state(clickData=None):
    figures = {}
    for key in canvas:
        if not key.startswith("aimodel"):
            fig = getattr(sim_plotter, f"plot_{key}")()
        elif key == "aimodel_response":
            func_name = getattr(aimodel_plotter, f"plot_{key}")
            label = clickData["points"][0]["y"] if clickData else None
            fig = aimodel_plotter.plot_aimodel_response(
                sim_plotter.aimodel_plotdata, label
            )
        else:
            func_name = getattr(aimodel_plotter, f"plot_{key}")
            fig = func_name(sim_plotter.aimodel_plotdata)

        figures[key] = fig

    return figures


@callback(
    Output("live-graphs", "children"),
    Input("interval-component", "n_intervals"),
    Input("aimodel_varimps", "clickData"),
)
# pylint: disable=unused-argument
def update_graph_live(n, clickData):
    state_id = get_latest_state_id()

    try:
        st, ts = sim_plotter.load_state(state_id)
    except Exception as e:
        return [
            html.Div(
                [html.H2(f"Error/waiting: {e}", id="sim_state_text")]
                + empty_graphs_template,
                id="live-graphs",
            ),
        ]

    figures = get_figures_by_state(clickData)

    return [
        html.H2(f"Simulation ID: {state_id}", id="sim_state_text"),
        html.H2(
            f"Iter #{st.iter_number} ({ts})" if ts != "final" else "Final sim state",
            id="sim_current_ts",
            className="finalState" if ts == "final" else "runningState",
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["pdr_profit_vs_time"]),
                dcc.Graph(figure=figures["trader_profit_vs_time"]),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["accuracy_vs_time"]),
            ]
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["pdr_profit_vs_ptrue"]),
                dcc.Graph(figure=figures["trader_profit_vs_ptrue"]),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["aimodel_varimps"], id="aimodel_varimps"),
                dcc.Graph(figure=figures["aimodel_response"]),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["f1_precision_recall_vs_time"]),
            ]
        ),
    ]


if __name__ == "__main__":
    app.run(debug=True)
