from dash import dcc, html
import dash_bootstrap_components as dbc


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


# pylint: disable=line-too-long
def get_column_graphs(figures: list[dict], title: str, tooltip: str):
    height_percentage = 80 / (len(figures) if (title != "ADF") else 2)
    return (
        html.Div(
            [
                html.Span(
                    children=title + " ⓘ",
                    id=figures[0]["graph_id"] + "-title",
                    style={
                        "textAlign": "center",
                        "fontSize": "18px",
                        "margin": "auto",
                        "cursour": "pointer",
                    },
                ),
                dbc.Tooltip(
                    dcc.Markdown(tooltip),
                    target=figures[0]["graph_id"] + "-title",
                ),
                *[
                    dcc.Graph(
                        figure=fig["fig"],
                        id=fig["graph_id"],
                        style={
                            "width": "100%",
                            "height": f"{fig['height'] if 'height' in fig and fig['height'] else height_percentage}vh",
                            "padding": "0",
                        },
                    )
                    for fig in figures
                ],
            ],
            style={
                "display": "flex",
                "flexDirection": "column",
                "alignItems": "center",
                "justifyContent": "center",
            },
        ),
    )


def display_on_column_graphs(div_id: str, width: str = "30%"):
    return html.Div(
        id=div_id,
        style={
            "display": "flex",
            "flexDirection": "column",
            "height": "100%",
            "width": width,
        },
    )


def get_input_elements():
    elements = html.Div(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id="feed-dropdown",
                        options=[],
                        value="",
                        style={
                            "width": "300px",
                            "fontSize": "22px",
                            "marginRight": "20px",
                            "height": "100%",
                        },
                    ),
                    # Date input components
                    dcc.DatePickerRange(
                        id="date-picker-range",
                        start_date=None,
                        end_date=None,
                        min_date_allowed=None,
                        max_date_allowed=None,
                    ),
                ],
                style={
                    "height": "100%",
                    "width": "100%",
                    "display": "flex",
                    "justifyContent": "flex-start",
                    "alignItems": "center",
                    "padding": "10px",
                },
            ),
            html.Div(
                [
                    html.Label("Lag", style={"fontSize": "20px"}),
                    dcc.Input(
                        id="autocorelation-lag",
                        type="number",
                        value="10",
                        style={
                            "width": "100px",
                            "fontSize": "22px",
                            "marginLeft": "20px",
                            "height": "100%",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "flex-start",
                    "alignItems": "center",
                },
            ),
        ],
        style={
            "height": "100%",
            "margin": "auto",
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "10px",
        },
    )

    return elements


def get_graphs_container():
    return html.Div(
        [
            display_on_column_graphs("transition_column", "22.5%"),
            display_on_column_graphs("seasonal_column", "50%"),
            display_on_column_graphs("autocorelation_column", "22.5%"),
        ],
        id="arima-graphs",
        style={
            "width": "100%",
            "display": "flex",
            "justifyContent": "space-between",
        },
    )
