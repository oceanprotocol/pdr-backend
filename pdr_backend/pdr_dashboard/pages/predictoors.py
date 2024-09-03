from typing import Any, Dict, List, Tuple

from dash import html, dash_table
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_search_bar,
)
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.pdr_dashboard.pages.common import TabularPage
from pdr_backend.pdr_dashboard.util.data import get_feed_column_ids
from pdr_backend.pdr_dashboard.util.format import format_table
from pdr_backend.pdr_dashboard.dash_components.modal import get_modal


class PredictoorsPage(TabularPage):
    def __init__(self, app):
        self.app = app

    def layout(self):
        return html.Div(
            [
                self.get_metrics_row(),
                self.get_search_bar_row(),
                self.get_main_container(),
                get_modal(
                    modal_id="predictoors_modal",
                ),
            ],
            className="page-layout",
        )

    def get_filters(self):
        return html.Div(
            [
                self.get_input_filter("APR"),
                self.get_input_filter("Accuracy", "predictoors"),
                self.get_input_filter("Nr Feeds"),
                self.get_input_filter("Staked"),
                self.get_input_filter("Gross Income"),
                self.get_input_filter("Stake Loss"),
                self.get_input_filter("Tx Costs"),
                self.get_input_filter("Net Income"),
            ],
            className="filters-container",
        )

    def get_filters_section(self):
        return html.Div(
            [
                self.get_filters(),
                html.Button(
                    "Clear All",
                    id="clear_predictoors_filters_button",
                    className="clear-filters-button",
                    style={
                        "width": "100px",
                        "hight": "100%",
                        "padding": "5px",
                    },
                ),
            ],
            className="filters-section",
            id="predictoors-filters-section",
        )

    def get_metrics_row(self):
        stats = self.app.db_getter.predictoors_stats(
            UnixTimeMs(self.app.start_date * 1000) if self.app.start_date else None
        )

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
                "search-input-predictoors-table", "Search for predictoors..."
            ),
            className="search-bar-row",
        )

    def get_main_container(self):
        res = self.app.db_getter.predictoor_payouts_stats(
            UnixTimeMs(self.app.start_date * 1000) if self.app.start_date else None
        )
        self.app.predictoors_data = res
        predictoor_cols, predictoor_data, raw_predictoor_data = (
            get_data_for_predictoors_table(self.app.predictoors_data, self.app.fee_cost)
        )

        self.app.predictoor_table_data = raw_predictoor_data

        return html.Div(
            [
                self.get_filters_section(),
                self.get_predictoor_table_area(predictoor_cols, predictoor_data),
            ],
            className="tabular-main-container",
        )

    def get_predictoor_table_area(
        self,
        columns,
        predictoor_data,
    ):
        return html.Div(
            [
                dash_table.DataTable(
                    id="predictoors_page_table",
                    columns=columns,
                    hidden_columns=["full_addr"],
                    row_selectable="single",
                    data=predictoor_data,
                    sort_action="custom",
                    sort_mode="single",
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )


def get_data_for_predictoors_table(
    predictoors_data, fee_cost
) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    new_predictoor_data = []

    if len(predictoors_data) == 0:
        return (
            [
                {"name": "Addr", "id": "addr"},
                {"name": "Full Addr", "id": "full_addr"},
                {"name": "Apr", "id": "apr"},
                {"name": "Accuracy", "id": "accuracy"},
                {"name": "Number Of Feeds", "id": "number_of_feeds"},
                {"name": "Staked (Ocean)", "id": "staked_(OCEAN)"},
                {"name": "Gross Income (Ocean)", "id": "gross_income_(OCEAN)"},
                {"name": "Stake Loss (Ocean)", "id": "stake_loss_(OCEAN)"},
                {"name": "Tx Costs (Ocean)", "id": "tx_costs_(OCEAN)"},
                {"name": "Net Income (Ocean)", "id": "net_income_(OCEAN)"},
            ],
            [],
            [],
        )

    ## split the pair column into two columns
    for data_item in predictoors_data:
        tx_costs = fee_cost * float(data_item["stake_count"])

        temp_pred_item = {}
        temp_pred_item["addr"] = str(data_item["user"])
        temp_pred_item["full_addr"] = str(data_item["user"])
        temp_pred_item["apr"] = data_item["apr"]
        temp_pred_item["accuracy"] = data_item["avg_accuracy"]
        temp_pred_item["number_of_feeds"] = str(data_item["feed_count"])
        temp_pred_item["staked_(OCEAN)"] = data_item["total_stake"]
        temp_pred_item["gross_income_(OCEAN)"] = data_item["gross_income"]
        temp_pred_item["stake_loss_(OCEAN)"] = data_item["stake_loss"]
        temp_pred_item["tx_costs_(OCEAN)"] = tx_costs
        temp_pred_item["net_income_(OCEAN)"] = data_item["total_profit"] - tx_costs

        new_predictoor_data.append(temp_pred_item)

    columns = get_feed_column_ids(new_predictoor_data[0])

    formatted_data = format_table(new_predictoor_data, columns)

    return columns, formatted_data, new_predictoor_data


def key_id_name(key: str) -> str:
    sanitized_key = key.lower().replace(" ", "_").replace("(avg)", "")

    return f"predictoors_page_{sanitized_key}_metric"
