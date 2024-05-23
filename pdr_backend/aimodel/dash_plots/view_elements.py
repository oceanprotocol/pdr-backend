from dash import dcc, html

figure_names = [
    "autocorelation",
    "partial_autocorelation",
]


def display_waiting_template():
    return html.Div(
        [html.H2("Loading data and creating charts...", id="wating-text")],
        id="wating",
    )


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
