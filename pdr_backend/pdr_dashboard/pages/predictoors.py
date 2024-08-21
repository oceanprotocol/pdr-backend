from typing import List, Dict, Any, Tuple

from dash import html, dash_table
import dash_bootstrap_components as dbc
from pdr_backend.pdr_dashboard.util.data import (
    get_feed_column_ids,
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
from pdr_backend.pdr_dashboard.pages.common import TabularPage
from pdr_backend.pdr_dashboard.util.prices import calculate_tx_gas_fee_cost_in_OCEAN


class PredictoorsPage(TabularPage):
    def __init__(self, app):
        self.app = app

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
                self.get_input_filter("APR"),
                self.get_input_filter("Accuracy", "predictoors"),
                self.get_input_filter("Gross Income"),
                self.get_input_filter("Nr Feeds"),
                self.get_input_filter("Stake"),
                self.get_input_filter("Costs"),
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
                "search-input-predictoors-table", "Search for predictoors..."
            ),
            className="search-bar-row",
        )

    def get_main_container(self):
        predictoor_stats = self.app.db_getter.predictoor_payouts_stats()

        predictoor_cols, predictoor_data, raw_predictoor_data = (
            self.get_data_for_predictoors_table(predictoor_stats)
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
                    sort_action="native",  # Enables sorting feature
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )

    def get_data_for_predictoors_table(
        self,
        predictoor_stats: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, Any]], List[Dict[str, Any]]]:

        temp_data = predictoor_stats

        new_predictoor_data = []

        appr_cost = calculate_tx_gas_fee_cost_in_OCEAN(
            self.app.web3_pp,
            "0x18f54cc21b7a2fdd011bea06bba7801b280e3151",
            self.app.prices,
        )

        ## split the pair column into two columns
        for data_item in temp_data:
            temp_pred_item = {}
            temp_pred_item["addr"] = str(data_item["user"])
            temp_pred_item["gross_income_(OCEAN)"] = data_item["total_payout"]
            temp_pred_item["accuracy"] = data_item["avg_accuracy"]
            temp_pred_item["staked_(OCEAN)"] = data_item["total_stake"]
            temp_pred_item["number_of_feeds"] = str(data_item["feed_count"])
            temp_pred_item["tx_costs_(OCEAN)"] = appr_cost * float(
                data_item["stake_count"]
            )
            temp_pred_item["income_from_stakes_(OCEAN)"] = data_item["total_profit"]
            temp_pred_item["apr"] = data_item["apr"]

            new_predictoor_data.append(temp_pred_item)

        columns = get_feed_column_ids(new_predictoor_data[0])

        formatted_data = format_table(new_predictoor_data, columns)

        return columns, formatted_data, new_predictoor_data

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
