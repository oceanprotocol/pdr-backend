from dash import dcc, html
from plotly.graph_objs import Figure

figure_names = [
    "pdr_profit_vs_time",
    "trader_profit_vs_time",
    "accuracy_vs_time",
    "pdr_profit_vs_ptrue",
    "trader_profit_vs_ptrue",
    "aimodel_varimps",
    "aimodel_response",
    "f1_precision_recall_vs_time",
    "log_loss_vs_time",
]

empty_selected_vars = dcc.Checklist([], [], id="selected_vars")

empty_graphs_template = html.Div(
    [dcc.Graph(figure=Figure(), id=key) for key in figure_names]
    + [empty_selected_vars],
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


def side_by_side_graphs(figures, name1, name2):
    return html.Div(
        [
            dcc.Graph(figure=figures[name1], id=name1, style={"width": "50%"}),
            dcc.Graph(figure=figures[name2], id=name2, style={"width": "50%"}),
        ],
        style={"display": "flex", "justifyContent": "space-between"},
    )


def arrange_figures(figures):
    return [
        side_by_side_graphs(figures, "pdr_profit_vs_time", "trader_profit_vs_time"),
        html.Div(
            [
                dcc.Graph(figure=figures["accuracy_vs_time"], id="accuracy_vs_time"),
            ]
        ),
        side_by_side_graphs(figures, "pdr_profit_vs_ptrue", "trader_profit_vs_ptrue"),
        side_by_side_graphs(figures, "aimodel_varimps", "aimodel_response"),
        side_by_side_graphs(figures, "f1_precision_recall_vs_time", "log_loss_vs_time"),
    ]


def selected_var_checklist(state_options, selected_vars_old):
    return dcc.Checklist(
        options=[{"label": var, "value": var} for var in state_options],
        value=selected_vars_old,
        id="selected_vars",
        style={"display": "none"},
    )
