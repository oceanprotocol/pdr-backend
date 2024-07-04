#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from dash import dcc, html
from enforce_typing import enforce_types
from plotly.graph_objs import Figure

OTHER_FIGURES = [
    "pdr_profit_vs_time",
    "pdr_profit_vs_ptrue",
    "trader_profit_vs_time",
    "trader_profit_vs_ptrue",
    "model_performance_vs_time",
]

MODEL_RESPONSE_FIGURES = [
    "aimodel_varimps_UP",
    "aimodel_response_UP",
    "aimodel_varimps_DOWN",
    "aimodel_response_DOWN",
]

FIGURE_NAMES = OTHER_FIGURES + MODEL_RESPONSE_FIGURES

EMPTY_SELECTED_VARS_UP = dcc.Checklist([], [], id="selected_vars_UP")
EMPTY_SELECTED_VARS_DOWN = dcc.Checklist([], [], id="selected_vars_DOWN")

EMPTY_GRAPHS_TEMPLATE = html.Div(
    [dcc.Graph(figure=Figure(), id=name) for name in FIGURE_NAMES]
    + [EMPTY_SELECTED_VARS_UP]
    + [EMPTY_SELECTED_VARS_DOWN],
    style={"display": "none"},
)


@enforce_types
def get_waiting_template(err):
    return html.Div(
        [html.H2(f"Error/waiting: {err}", id="sim_state_text")]
        + [EMPTY_GRAPHS_TEMPLATE],
        id="live-graphs",
    )


@enforce_types
def get_header_elements(run_id, st, ts):
    return [
        html.H2(
            f"Simulation ID: {run_id}",
            id="sim_state_text",
            style={"fontSize": "18px", "marginTop": ".5rem"},
        ),
        html.H3(
            f"Iter #{st.iter_number} ({ts})" if ts != "final" else "Final sim state",
            id="sim_current_ts",
            # stops refreshing if final state was reached. Do not remove this class!
            className="finalState" if ts == "final" else "runningState",
            style={"marginTop": "0", "textAlign": "center", "fontSize": "18px"},
        ),
    ]


@enforce_types
def side_by_side_graphs(
    figures,
    name1: str,
    name2: str,
    height: str = "50%",
    width1: str = "50%",
    width2: str = "50%",
):
    return html.Div(
        [
            dcc.Graph(figure=figures[name1], id=name1, style={"width": width1}),
            dcc.Graph(figure=figures[name2], id=name2, style={"width": width2}),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "width": "100%",
            "height": height,
        },
    )


@enforce_types
def single_graph(figures, name: str, width: str):
    return html.Div(
        [
            dcc.Graph(
                figure=figures[name],
                id=name,
                style={"width": "100%", "height": "100%"},
            ),
        ],
        style={"width": width, "height": "100%"},
    )


@enforce_types
def get_tabs(figures):
    return [
        {
            "name": "Predictoor Profit",
            "components": [
                single_graph(figures, "pdr_profit_vs_time", width="100%"),
                single_graph(figures, "pdr_profit_vs_ptrue", width="100%"),
            ],
            "className": "predictor_profit_tab",
        },
        {
            "name": "Trader Profit",
            "components": [
                single_graph(figures, "trader_profit_vs_time", width="100%"),
                single_graph(figures, "trader_profit_vs_ptrue", width="100%"),
            ],
            "className": "trader_profit_tab",
        },
        {
            "name": "Model performance",
            "components": [
                single_graph(figures, "model_performance_vs_time", "100%"),
            ],
            "className": "model_performance_tab",
        },
        {
            "name": "Model response",
            "components": [
                side_by_side_graphs(
                    figures,
                    name1="aimodel_varimps_UP",
                    name2="aimodel_response_UP",
                    height="100%",
                    width1="30%",
                    width2="70%",
                ),
                side_by_side_graphs(
                    figures,
                    name1="aimodel_varimps_DOWN",
                    name2="aimodel_response_DOWN",
                    height="100%",
                    width1="30%",
                    width2="70%",
                ),
            ],
            "className": "model_response_tab",
        },
    ]


@enforce_types
def selected_var_UP_checklist(state_options, selected_vars_UP_old):
    return dcc.Checklist(
        options=[{"label": var, "value": var} for var in state_options],
        value=selected_vars_UP_old,
        id="selected_vars_UP",
        style={"display": "none"},
    )


@enforce_types
def selected_var_DOWN_checklist(state_options, selected_vars_DOWN_old):
    return dcc.Checklist(
        options=[{"label": var, "value": var} for var in state_options],
        value=selected_vars_DOWN_old,
        id="selected_vars_DOWN",
        style={"display": "none"},
    )


@enforce_types
def get_tabs_component(elements, selectedTab):
    return dcc.Tabs(
        id="tabs",
        value=selectedTab,
        children=[
            dcc.Tab(
                label=e["name"],
                value=e["name"],
                children=e["components"],
                style={"width": "200px"},
                selected_style={"borderLeft": "4px solid blue"},
                className=e["className"],
            )
            for e in elements
        ],
        vertical=True,
        style={"fontSize": "16px"},
        content_style={
            "width": "100%",
            "height": "100%",
            "borderLeft": "1px solid #d6d6d6",
            "borderTop": "1px solid #d6d6d6",
        },
        parent_style={"width": "100%", "height": "100%"},
    )


@enforce_types
def get_main_container():
    return html.Div(
        [
            html.Div(
                EMPTY_GRAPHS_TEMPLATE,
                id="header",
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "height": "60px",
                },
            ),
            html.Div(
                id="tabs-container",
                style={"height": "calc(100% - 60px)"},
            ),
        ],
        id="main-container",
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "flexStart",
            "alignIntems": "start",
            "height": "100%",
        },
    )


@enforce_types
def get_layout():
    return html.Div(
        [
            get_main_container(),
            dcc.Interval(
                id="interval-component",
                interval=3 * 1000,  # in milliseconds
                n_intervals=0,
                disabled=False,
            ),
            dcc.Store(id="selected-tab"),
        ],
        style={"height": "100vh"},
    )
