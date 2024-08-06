from typing import List, Dict, Any, Tuple

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.util.data import (
    col_to_human,
    find_with_key_value,
)

from pdr_backend.pdr_dashboard.dash_components.view_elements import get_metric
from pdr_backend.pdr_dashboard.util.format import format_table


class FeedsPage:
    def __init__(self, app):
        self.app = app

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
        )

    def get_main_container(self):
        feed_stats = self.app.db_getter.feed_payouts_stats()
        feed_subscriptions = self.app.db_getter.feed_subscription_stats(
            self.app.network_name
        )

        feed_cols, feed_data = self.get_feeds_data_for_feeds_table(
            feed_stats, feed_subscriptions
        )

        return html.Div(
            [self.get_feeds_table_area(feed_cols, feed_data)],
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
                    id="feeds_table",
                    columns=columns,
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
                "avg_accuracy": result["avg_accuracy"],
                "avg_stake_(OCEAN)": result["avg_stake"],
                "volume_(OCEAN)": result["volume"],
            }

        return {
            "avg_accuracy": 0,
            "avg_stake_(OCEAN)": 0,
            "volume_(OCEAN)": 0,
        }

    def get_feeds_subscription_stat_with_contract(
        self, contract: str, feed_subcription_stats: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        result = find_with_key_value(feed_subcription_stats, "contract", contract)

        if result:
            return {
                "price_(OCEAN)": result["price"],
                "sales": f"{result['sales']} ({result['df_buy_count']}-DF)",
                "sales_revenue_(OCEAN)": result["sales_revenue"],
            }

        return {
            "price_(OCEAN)": 0,
            "sales": 0,
            "sales_revenue_(OCEAN)": 0,
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

        formatted_data = format_table(new_feed_data, columns)

        return columns, formatted_data
