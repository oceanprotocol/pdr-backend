from dash import dcc, html
from plotly.graph_objs import Figure

from pdr_backend.sim.sim_plotter import SimPlotter

figure_names = [
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

empty_selected_vars = dcc.Checklist([], [], id="selected_vars")

non_final_state_div = html.Div(
    [empty_slider, empty_selected_vars],
    style={"display": "none"},
)


empty_graphs_template = html.Div(
    [dcc.Graph(figure=Figure(), id=key) for key in figure_names]
    + [empty_slider, empty_selected_vars],
    style={"display": "none"},
)


def get_waiting_template(err):
    return html.Div(
        [html.H2(f"Error/waiting: {err}", id="sim_state_text")]
        + [empty_graphs_template],
        id="live-graphs",
    )


def get_header_elements(run_id, st, ts):
    return [
        html.H2(f"Simulation ID: {run_id}", id="sim_state_text"),
        html.H2(
            f"Iter #{st.iter_number} ({ts})" if ts != "final" else "Final sim state",
            id="sim_current_ts",
            # stops refreshing if final state was reached. Do not remove this class!
            className="finalState" if ts == "final" else "runningState",
        ),
    ]


def arrange_figures(figures):
    return [
        html.Div(
            [
                dcc.Graph(figure=figures["pdr_profit_vs_time"]),
                dcc.Graph(figure=figures["trader_profit_vs_time"]),
            ],
            style={"display": "flex", "justifyContent": "space-between"},
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
            style={"display": "flex", "justifyContent": "space-between"},
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["aimodel_varimps"], id="aimodel_varimps"),
                dcc.Graph(figure=figures["aimodel_response"]),
            ],
            style={"display": "flex", "justifyContent": "space-between"},
        ),
        html.Div(
            [
                dcc.Graph(figure=figures["f1_precision_recall_vs_time"]),
            ]
        ),
    ]


def snapshot_slider(run_id, set_ts, slider_value):
    snapshots = SimPlotter.available_snapshots(run_id)[:-1]
    marks = {i: f"{s.replace('_', '')[:-4]}" for i, s in enumerate(snapshots)}
    marks[len(snapshots)] = "final"

    return dcc.Slider(
        id="state_slider",
        marks=marks,
        value=len(snapshots) if not set_ts else slider_value,
        step=1,
    )


def selected_var_checklist(state_options, selected_vars_old):
    return dcc.Checklist(
        options=[{"label": var, "value": var} for var in state_options],
        value=selected_vars_old,
        id="selected_vars",
        style={"display": "none"},
    )
