from typing import List, Dict, Any, Union, Tuple

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.dash_components.util import (
    get_feed_payouts_stats_from_db,
    get_feed_subscription_stats_from_db,
    col_to_human,
    find_with_key_value,
)


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
                        self.get_main_container(),
                    ],
                    custom_spinner=html.H2(dbc.Spinner(), style={"height": "100%"}),
                ),
            ],
            style={"height": "100%"},
        )

    def get_main_container(self):
        feed_stats = get_feed_payouts_stats_from_db(self.app.lake_dir)
        feed_subscriptions = get_feed_subscription_stats_from_db(
            self.app.lake_dir, self.app.network_name
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
    ) -> Union[Tuple[float, float, float], None]:
        result = find_with_key_value(feed_stats, "contract", contract)

        if result:
            return (
                round(result["avg_accuracy"], 2),
                round(result["volume"], 2),
                round(result["avg_stake"], 2),
            )

        return None

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

            feed_item["avg_accuracy"] = str(result[0]) + "%" if result else ""
            feed_item["avg_stake_(OCEAN)"] = result[2] if result else ""
            feed_item["volume_(OCEAN)"] = result[1] if result else ""

            subscription_result = find_with_key_value(
                feed_subcription_stats, "contract", feed["contract"]
            )

            feed_item["price_(OCEAN)"] = (
                subscription_result["price"] if subscription_result else ""
            )
            feed_item["sales"] = (
                (
                    f"{subscription_result['sales']} ({subscription_result['df_buy_count']}-DF)"
                )
                if subscription_result
                else ""
            )
            feed_item["sales_revenue_(OCEAN)"] = (
                subscription_result["sales_revenue"] if subscription_result else ""
            )

            new_feed_data.append(feed_item)

        columns = [
            {"name": col_to_human(col), "id": col} for col in new_feed_data[0].keys()
        ]

        return columns, new_feed_data
