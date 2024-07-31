from dash import html, dcc
import dash_bootstrap_components as dbc

options_ex = [
    {"label": "Option 1", "value": "OPT1"},
    {"label": "Option 2", "value": "OPT2"},
    {"label": "Option 3", "value": "OPT3"},
    {"label": "Option 4", "value": "OPT4"},
]


class Filter:
    def __init__(self, name, placeholder, options):
        self.name = name
        self.placeholder = placeholder
        self.options = options


filters = [
    {"name": "base_token", "placeholder": "Base Token", "options": options_ex},
    {"name": "quote_token", "placeholder": "Quote Token", "options": options_ex},
    {"name": "venue", "placeholder": "Venue", "options": options_ex},
    {"name": "time", "placeholder": "Time", "options": options_ex},
]

filters_objects = [Filter(**item) for item in filters]


class FeedsPage:
    def layout(self):
        return html.Div(
            [
                dcc.Store(id="user-payout-stats"),
                html.H1(
                    "Feeds page content",
                    id="page_title_feeds",
                ),
                dcc.Loading(
                    id="loading",
                    type="default",
                    children=[],
                    custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
                ),
                self.get_filters_section(),
            ],
            style={"height": "100%"},
        )

    def get_multiselect_dropdown(self, filter_obj: Filter):
        return dcc.Dropdown(
            id=filter_obj.name,
            options=filter_obj.options,
            multi=True,
            placeholder=filter_obj.placeholder,
            style={"width": "130px", "borderColor": "#aaa"},
        )

    def get_filters(self):
        return html.Div(
            [
                self.get_multiselect_dropdown(filter_obj)
                for filter_obj in filters_objects
            ]
            + [
                self.get_input_filter("Sales"),
                self.get_input_filter("Revenue"),
                self.get_input_filter("Accuracy"),
                self.get_input_filter("Volume"),
            ],
            style={
                "width": "100%",
                "display": "flex",
                "justofyContnet": "center",
                "alignItems": "flex_start",
                "gap": "8px",
            },
        )

    def get_input_filter(self, label: str):
        return dbc.DropdownMenu(
            [
                self.get_input_with_label("Min"),
                self.get_input_with_label("Max"),
                html.Button(
                    "Apply Filter",
                    style={
                        "width": "100%",
                        "padding": "5px",
                    },
                ),
            ],
            label=label,
            style={
                "backgroundColor": "white",
            },
            toggle_style={
                "width": "120px",
                "backgroundColor": "white",
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            },
        )

    def get_input_with_label(self, label: str):
        return html.Div(
            [html.Label(label), dcc.Input(id=label.lower())],
            style={
                "display": "flex",
                "flexDirection": "column",
                "justifyContent": "center",
                "alignItems": "flex-start",
                "padding": "10px",
            },
        )

    def get_filters_section(self):
        return html.Div(
            [
                self.get_filters(),
                html.Button(
                    "Clear All",
                    style={
                        "width": "100px",
                        "hight": "100%",
                        "padding": "5px",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
            },
        )
