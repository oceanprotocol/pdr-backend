from dash import html, dcc
import dash_bootstrap_components as dbc

options_ex = [
    {"label": "Option 1", "value": "OPT1"},
    {"label": "Option 2", "value": "OPT2"},
    {"label": "Option 3", "value": "OPT3"},
    {"label": "Option 4", "value": "OPT4"},
]


def add_to_filter(filter_options, value):
    if value not in filter_options:
        filter_options.append(value)


class Filter:
    def __init__(self, name, placeholder, options):
        self.name = name
        self.placeholder = placeholder
        self.options = options


filters = [
    {"name": "base_token", "placeholder": "Base Token", "options": []},
    {"name": "quote_token", "placeholder": "Quote Token", "options": []},
    {"name": "venue", "placeholder": "Venue", "options": []},
    {"name": "time", "placeholder": "Time", "options": []},
]

filters_objects = [Filter(**item) for item in filters]


class FeedsPage:
    def __init__(self, app):
        self.app = app

        for feed in app.feeds_data:
            pair_base, pair_quote = feed["pair"].split("/")

            # Update base currency filter
            add_to_filter(filters[0]["options"], pair_base)

            # Update quote currency filter
            add_to_filter(filters[1]["options"], pair_quote)

            # Update source filter
            add_to_filter(filters[2]["options"], feed["source"])

            # Update timeframe filter
            add_to_filter(filters[3]["options"], feed["timeframe"])

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
            value=[],
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
                self.get_input_with_label("Min", label),
                self.get_input_with_label("Max", label),
                html.Button(
                    "Apply Filter",
                    style={
                        "width": "100%",
                        "padding": "5px",
                    },
                    id=f"{label.lower()}_button",
                ),
            ],
            id=f"{label.lower()}_dropdown",
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

    def get_input_with_label(self, label: str, name: str):
        return html.Div(
            [html.Label(label), dcc.Input(id=f"{name.lower()}_{label.lower()}")],
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
                    id="clear_filters_button",
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
