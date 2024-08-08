from typing import List, Dict, Any, Tuple

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.util.data import (
    col_to_human,
    find_with_key_value,
)

from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_graph,
)


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
    {"name": "exchange", "placeholder": "Exchange", "options": []},
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
            add_to_filter(filters[2]["options"], feed["source"].capitalize())

            # Update timeframe filter
            add_to_filter(filters[3]["options"], feed["timeframe"])

    def layout(self):
        return html.Div(
            [
                dcc.Store(id="user-payout-stats"),
                dcc.Loading(
                    id="loading",
                    type="default",
                    children=[
                        self.get_metrics_row(),
                        self.get_main_container(),
                        self.get_modal(),
                    ],
                    custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
                ),
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
            style={"width": "140px", "borderColor": "#aaa"},
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
            id="filters-container",
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
            toggleClassName="dropdown-toggle-container",
        )

    def get_input_with_label(self, label: str, name: str):
        return html.Div(
            [html.Label(label), dcc.Input(id=f"{name.lower()}_{label.lower()}")],
            className="input-with-label",
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
            id="filters-section",
        )

    def get_metrics_row(self):
        stats = self.app.db_getter.feeds_stats()

        return html.Div(
            children=[
                get_metric(
                    label=key,
                    value=value,
                    value_id=f"feeds_page_{key}_metric",
                )
                for key, value in stats.items()
            ],
            id="feeds_page_metrics_row",
            style={"marginBottom": "60px"},
        )

    def get_main_container(self):
        feed_stats = self.app.db_getter.feed_payouts_stats()
        feed_subscriptions = self.app.db_getter.feed_subscription_stats(
            self.app.network_name
        )

        feed_cols, feed_data = self.get_feeds_data_for_feeds_table(
            feed_stats, feed_subscriptions
        )

        self.app.feeds_table_data = feed_data

        return html.Div(
            [
                self.get_filters_section(),
                self.get_feeds_table_area(feed_cols, feed_data),
            ],
            id="feeds-main-container",
            className="main-container",
        )

    def get_feeds_table_area(
        self,
        columns,
        feeds_data,
    ):
        return html.Div(
            [
                dash_table.DataTable(
                    id="feeds_page_table",
                    columns=columns,
                    hidden_columns=["full_addr"],
                    row_selectable="single",
                    data=feeds_data,
                    sort_action="native",  # Enables sorting feature
                )
            ],
            style={"width": "100%"},
        )

    def get_feeds_stat_with_contract(
        self, contract: str, feed_stats: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        result = find_with_key_value(feed_stats, "contract", contract)

        if result:
            return {
                "avg_accuracy": str(round(result["avg_accuracy"], 2)) + "%",
                "avg_stake_(OCEAN)": str(round(result["avg_stake"], 2)),
                "volume_(OCEAN)": str(round(result["volume"], 2)),
            }

        return {
            "avg_accuracy": "",
            "avg_stake_(OCEAN)": "",
            "volume_(OCEAN)": "",
        }

    def get_feeds_subscription_stat_with_contract(
        self, contract: str, feed_subcription_stats: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        result = find_with_key_value(feed_subcription_stats, "contract", contract)

        if result:
            return {
                "price_(OCEAN)": str(result["price"]),
                "sales": f"{result['sales']} ({result['df_buy_count']}-DF)",
                "sales_revenue_(OCEAN)": str(result["sales_revenue"]),
            }

        return {
            "price_(OCEAN)": "",
            "sales": "",
            "sales_revenue_(OCEAN)": "",
        }

    def get_feeds_data_for_feeds_table(
        self,
        feed_stats: List[Dict[str, Any]],
        feed_subcription_stats: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]]]:

        temp_data = self.app.feeds_data

        new_feed_data = []
        ## split the pair column into two columns
        for feed in temp_data:
            split_pair = feed["pair"].split("/")
            feed_item = {}
            feed_item["addr"] = feed["contract"][:5] + "..." + feed["contract"][-5:]
            feed_item["base_token"] = split_pair[0]
            feed_item["quote_token"] = split_pair[1]
            feed_item["exchange"] = feed["source"].capitalize()
            feed_item["time"] = feed["timeframe"]
            feed_item["full_addr"] = feed["contract"]

            result = self.get_feeds_stat_with_contract(feed["contract"], feed_stats)

            feed_item.update(result)

            subscription_result = self.get_feeds_subscription_stat_with_contract(
                feed["contract"], feed_subcription_stats
            )

            feed_item.update(subscription_result)

            new_feed_data.append(feed_item)

        columns = [
            {"name": col_to_human(col), "id": col} for col in new_feed_data[0].keys()
        ]

        return columns, new_feed_data

    def get_modal(self):
        return dbc.Modal(
            [
                dbc.ModalHeader("Header"),
                dbc.ModalBody("This is the content of the modal", id="modal_body"),
            ],
            id="modal",
        )

    def get_feed_graphs_modal_header(self, selected_row):
        return html.Div(
            html.Span(
                f'{selected_row["base_token"]}-{selected_row["quote_token"]} {selected_row["time"]} {selected_row["exchange"]}',
                style={"fontWeight": "bold", "fontSize": "20px"},
            ),
            style={
                "display": "flex",
                "justifyContent": "center",
                "width": "100%",
                "padding": "10px",
            },
        )

    def get_feed_graphs_modal_body(self, figures):
        return html.Div([get_graph(fig) for fig in figures])
