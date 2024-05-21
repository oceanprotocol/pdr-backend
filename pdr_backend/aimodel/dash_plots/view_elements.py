from dash import dcc, html
from plotly.graph_objs import Figure

figure_names = [
    "autocorelation",
    "partial_autocorelation",
]

empty_graphs_template = html.Div(
    [dcc.Graph(figure=Figure(), id=key) for key in figure_names],
    style={"display": "none"},
)


def get_waiting_template(err):
    return html.Div(
        [html.H2(f"Error/waiting: {err}", id="sim_state_text")],
        id="live-graphs",
    )


def get_header_elements():
    return [
        html.H2(
            "ARIMA feed data",
            id="sim_current_ts",
            # stops refreshing if final state was reached. Do not remove this class!
            className="finalState",
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
        side_by_side_graphs(figures, "autocorelation", "partial_autocorelation"),
    ]