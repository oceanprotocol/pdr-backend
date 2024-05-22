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


def display_on_column_graphs(figures: list[dict]):
    return html.Div(
        [
            dcc.Graph(figure=fig["fig"], id=fig["graph_id"], style={"width": "50%"})
            for fig in figures
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "justifyContent": "space-between",
        },
    )
