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
        [html.H1(f"Error/waiting: {err}", id="sim_state_text")],
        id="live-graphs",
    )


def get_header_elements():
    return [
        html.H1(
            "ARIMA feed data",
            id="page_title",
            # stops refreshing if final state was reached. Do not remove this class!
            className="title",
            style={"width": "100%", "text-align": "center"},
        ),
    ]


def display_plots_view(columns):
    return html.Div(
        columns,
        id="plots_container",
        style={
            "display": "flex",
            "flexWrap": "wrap",
            "justifyContent": "space-around",
        },
    )


def display_on_column_graphs(figures: list[dict]):
    height_percentage = 90 / (len(figures) if (len(figures) > 1) else 2)
    return html.Div(
        [
            dcc.Graph(
                figure=fig["fig"],
                id=fig["graph_id"],
                style={
                    "width": "100%",
                    "height": f"{height_percentage}vh",
                    "padding": "0",
                },
            )
            for fig in figures
        ],
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
            "width": "30%",
        },
    )
