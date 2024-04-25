import os
from pathlib import Path
import sys

import plotly
from dash import Dash, Input, Output, State, callback, dcc, html

from pdr_backend.aimodel import aimodel_plotter
from pdr_backend.sim.sim_plotter import SimPlotter

# TODO: handle clickdata in varimps callback
# TODO: CSS/HTML layout tweaks


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

empty_slider = dcc.Slider(
    id="state_slider",
    min=0,
    max=0,
    step=1,
    disabled=True,
)

empty_slider_div = html.Div([empty_slider], style={"display": "none"})


empty_graphs_template = html.Div(
    [dcc.Graph(figure=plotly.graph_objs.Figure(), id=key) for key in canvas]
    + [empty_slider],
    style={"display": "none"},
)


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


def get_all_state_names():
    path = Path("sim_state").iterdir()
    return [str(p).replace("sim_state/", "") for p in path]


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
    Input("state_slider", "value"),
)
# pylint: disable=unused-argument
def update_graph_live(n, clickData, slider_value):
    global g_state_id

    state_id = get_latest_state_id() if g_state_id is None else g_state_id
    set_ts = None

    if slider_value is not None:
        snapshots = SimPlotter.available_snapshots(state_id)
        set_ts = snapshots[slider_value]

    try:
        st, ts = sim_plotter.load_state(state_id, set_ts)
    except Exception as e:
        return [
            html.Div(
                [html.H2(f"Error/waiting: {e}", id="sim_state_text")]
                + [empty_graphs_template],
                id="live-graphs",
            ),
        ]

    elements = [
        html.H2(f"Simulation ID: {state_id}", id="sim_state_text"),
        html.H2(
            f"Iter #{st.iter_number} ({ts})" if ts != "final" else "Final sim state",
            id="sim_current_ts",
            className="finalState" if ts == "final" else "runningState",
        ),
    ]

    if ts == "final":
        # display slider if not in final state
        snapshots = SimPlotter.available_snapshots(state_id)[:-1]
        marks = {i: f"{s.replace('_', '')[:-4]}" for i, s in enumerate(snapshots)}
        marks[len(snapshots)] = "final"

        elements.append(
            dcc.Slider(
                id="state_slider",
                marks=marks,
                value=len(snapshots) if not set_ts else slider_value,
                step=1,
            )
        )
    else:
        elements.append(empty_slider_div)

    figures = get_figures_by_state(clickData)
    elements = elements + [
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

    return elements


if __name__ == "__main__":
    msg = "USAGE: python sim_plots.py [state_id] [port]"

    if len(sys.argv) > 3:
        print(msg)
        sys.exit(1)

    if len(sys.argv) == 3:
        state_id = sys.argv[1]
        if state_id not in get_all_state_names():
            print("Invalid state_id")
            sys.exit(1)
        port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        state_id = sys.argv[1]
        port = None
        if state_id not in get_all_state_names():
            state_id = None
            port = int(sys.argv[1])
    else:
        state_id = None
        port = 8050

    global g_state_id
    g_state_id = state_id

    app.run(debug=True, port=port)
