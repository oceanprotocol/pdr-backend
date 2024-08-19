from typing import List, Dict, Any, Tuple, Union

from dash import html, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.util.data import (
    get_feed_column_ids,
    find_with_key_value,
)
from pdr_backend.pdr_dashboard.dash_components.plots import (
    FeedModalFigures,
)
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_graph,
    get_search_bar,
)
from pdr_backend.pdr_dashboard.util.format import format_table
from pdr_backend.pdr_dashboard.pages.common import TabularPage, Filter, add_to_filter


filters = [
    {"name": "apy", "placeholder": "APY", "options": []},
    {"name": "accuracy", "placeholder": "Accuracy", "options": []},
    {"name": "gross_income", "placeholder": "Gross Income", "options": []},
    {"name": "costs", "placeholder": "Costs", "options": []},
]

filters_objects = [Filter(**item) for item in filters]


class PredictoorsPage(TabularPage):
    def __init__(self, app):
        self.app = app
        # TODO: add_to_filter

    def layout(self):
        return html.Div(
            [
                self.get_metrics_row(),
                self.get_search_bar_row(),
                self.get_main_container(),
                self.get_modal(),
            ],
            className="page-layout",
        )

    def get_filters(self):
        return html.Div(
            [
                self.get_multiselect_dropdown(filter_obj)
                for filter_obj in filters_objects
            ]
            + [
                self.get_input_filter("Nr Feeds"),
                self.get_input_filter("Stake"),
            ],
            className="filters-container",
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
        stats = self.app.db_getter.predictoors_stats()

        return html.Div(
            children=[
                get_metric(
                    label=key,
                    value=value,
                    value_id=key_id_name(key),
                )
                for key, value in stats.items()
            ],
            className="metrics_row",
            id="predictoors_page_metrics_row",
        )

    def get_search_bar_row(self):
        return html.Div(
            children=get_search_bar(
                "search-input-feeds-table", "Search for predictoors..."
            ),
            className="search-bar-row",
        )

    def get_main_container(self):
        # TODO: replace with predictoors data
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
            className="tabular-main-container",
        )

    def get_feeds_table_area(
        self,
        columns,
        feeds_data,
    ):
        # TODO: replace with predictoors data, modify function name, parameters, id of table
        return html.Div(
            [
                dash_table.DataTable(
                    id="feeds_page_table",
                    columns=columns,
                    hidden_columns=["full_addr", "sales_raw"],
                    row_selectable="single",
                    data=feeds_data,
                    sort_action="native",  # Enables sorting feature
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )

    def get_feeds_stat_with_contract(
        self, contract: str, feed_stats: List[Dict[str, Any]]
    ) -> Dict[str, Union[float, int]]:
        # TODO: remove/adjust
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
        # TODO: remove/adjust
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
                counts_str = "_".join(
                    filter(None, [df_buy_count_str, ws_buy_count_str])
                )

                if counts_str:
                    sales_str += f"_{counts_str}"

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
        # TODO: remove/adjust

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
            feed_item["full_addr"] = feed["contract"]

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

    # TODO: remove/adjust everything below
    def get_modal(self):
        return dbc.Modal(
            self.get_default_modal_content(),
            id="modal",
        )

    def get_default_modal_content(self):
        figures = FeedModalFigures()
        return [
            dbc.ModalHeader("Loading feed data", id="feeds-modal-header"),
            self.get_feed_graphs_modal_body(figures.get_figures()),
        ]

    def get_feed_graphs_modal_header(self, selected_row):
        return html.Div(
            html.Span(
                f"""{selected_row["base_token"]}-{selected_row["quote_token"]}
                {selected_row["time"]} {selected_row["exchange"]}
                """,
                style={"fontWeight": "bold", "fontSize": "20px"},
            ),
            id="feeds-modal-header",
        )

    def get_feed_graphs_modal_body(self, figures):
        return html.Div(
            [
                html.Div(get_graph(fig), style={"width": "45%", "margin": "0 auto"})
                for fig in figures
            ],
            id="feeds-modal-body",
        )


def key_id_name(key: str) -> str:
    sanitized_key = key.lower().replace(" ", "_").replace("(avg)", "")

    return f"predictoors_page_{sanitized_key}_metric"
