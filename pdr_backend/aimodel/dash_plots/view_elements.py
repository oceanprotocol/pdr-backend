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


def get_input_elements():
    elements = html.Div(
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
            "margin": "auto",
            "display": "flex",
            "justifyContent": "flex-start",
            "alignItems": "center",
            "padding": "10px",
        },
    )

    return elements
