from typing import List, Dict, Any, Tuple, Union

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.util.data import (
    get_feed_column_ids,
    find_with_key_value,
)

from pdr_backend.pdr_dashboard.dash_components.view_elements import get_metric
from pdr_backend.pdr_dashboard.util.format import format_table


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

        feed_cols, feed_data, raw_feed_data = self.get_feeds_data_for_feeds_table(
            feed_stats, feed_subscriptions
        )

        self.app.feeds_table_data = raw_feed_data

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
                    hidden_columns=["sales_raw"],
                    data=feeds_data,
                    sort_action="native",  # Enables sorting feature
                )
            ],
            style={"width": "100%"},
        )

    def get_feeds_stat_with_contract(
        self, contract: str, feed_stats: List[Dict[str, Any]]
    ) -> Dict[str, Union[float, int]]:
        result = find_with_key_value(feed_stats, "contract", contract)

        if result:
            return {
                "avg_accuracy": float(result["avg_accuracy"]),
                "avg_stake_per_epoch_(OCEAN)": float(result["avg_stake"]),
                "volume_(OCEAN)": float(result["volume"]),
            }

        return {
            "avg_accuracy": 0,
            "avg_stake_per_epoch_(OCEAN)": 0,
            "volume_(OCEAN)": 0,
        }

    def get_feeds_subscription_stat_with_contract(
        self, contract: str, feed_subcription_stats: List[Dict[str, Any]]
    ) -> Dict[str, Union[float, int, str]]:
        result = find_with_key_value(feed_subcription_stats, "contract", contract)

        if result:
            sales_str = f"{result['sales']}"

            df_buy_count_str = (
                f"{result['df_buy_count']}-DF" if result["df_buy_count"] > 0 else ""
            )
            ws_buy_count_str = (
                f"{result['ws_buy_count']}-WS" if result["ws_buy_count"] > 0 else ""
            )

            if df_buy_count_str or ws_buy_count_str:
                counts_str = ", ".join(
                    filter(None, [df_buy_count_str, ws_buy_count_str])
                )
                sales_str += f" ({counts_str})"

            return {
                "price_(OCEAN)": result["price"],
                "sales": sales_str,
                "sales_raw": result["sales"],
                "sales_revenue_(OCEAN)": result["sales_revenue"],
            }

        return {
            "price_(OCEAN)": 0,
            "sales": 0,
            "sales_raw": 0,
            "sales_revenue_(OCEAN)": 0,
        }

    def get_feeds_data_for_feeds_table(
        self,
        feed_stats: List[Dict[str, Any]],
        feed_subcription_stats: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        temp_data = self.app.feeds_data

        new_feed_data = []
        ## split the pair column into two columns
        for feed in temp_data:
            split_pair = feed["pair"].split("/")
            feed_item = {}
            feed_item["addr"] = feed["contract"]
            feed_item["base_token"] = split_pair[0]
            feed_item["quote_token"] = split_pair[1]
            feed_item["exchange"] = feed["source"].capitalize()
            feed_item["time"] = feed["timeframe"]

            result = self.get_feeds_stat_with_contract(feed["contract"], feed_stats)

            feed_item.update(result)

            subscription_result = self.get_feeds_subscription_stat_with_contract(
                feed["contract"], feed_subcription_stats
            )

            feed_item.update(subscription_result)

            new_feed_data.append(feed_item)

        columns = get_feed_column_ids(new_feed_data[0])

        formatted_data = format_table(new_feed_data, columns)

        return columns, formatted_data, new_feed_data
