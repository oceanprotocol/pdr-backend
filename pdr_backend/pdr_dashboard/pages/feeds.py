from dash import dash_table, html

from pdr_backend.pdr_dashboard.dash_components.modal import get_modal
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_search_bar,
    table_initial_spinner,
)
from pdr_backend.pdr_dashboard.pages.common import TabularPage
from pdr_backend.pdr_dashboard.util.format import FEEDS_TABLE_COLS
from pdr_backend.pdr_dashboard.util.helpers import get_empty_feeds_filters


class FeedsPage(TabularPage):
    def __init__(self, app):
        self.app = app
        self.initial_filters = get_empty_feeds_filters()

    def layout(self):
        return html.Div(
            [
                self.get_metrics_row(),
                self.get_search_bar_row(),
                self.get_main_container(),
                get_modal(
                    modal_id="feeds_modal",
                ),
            ],
            className="page-layout",
        )

    def get_filters(self):
        return html.Div(
            [
                self.get_multiselect_dropdown(filter_obj)
                for filter_obj in self.initial_filters
            ]
            + [
                self.get_input_filter("Accuracy"),
                self.get_input_filter("Volume"),
                self.get_input_filter("Sales"),
                self.get_input_filter("Revenue"),
            ],
            className="filters-container",
        )

    def get_filters_section(self):
        return html.Div(
            [
                self.get_filters(),
                html.Button(
                    "Clear All",
                    id="clear_feeds_filters_button",
                    className="clear-filters-button",
                    style={
                        "width": "100px",
                        "hight": "100%",
                        "padding": "5px",
                    },
                ),
            ],
            className="filters-section",
            id="feeds-filters-section",
        )

    def get_metrics_row(self):
        return html.Div(
            children=[
                get_metric(
                    label=key,
                    value_id=f"feeds_page_{key}_metric",
                )
                for key in ["Feeds", "Accuracy", "Volume", "Sales", "Revenue"]
            ],
            className="metrics_row",
            id="feeds_page_metrics_row",
        )

    def get_search_bar_row(self):
        return html.Div(
            children=get_search_bar(
                "search-input-feeds-table", "Search for addrs, token ..."
            ),
            className="search-bar-row",
        )

    def get_main_container(self):
        return html.Div(
            [
                self.get_filters_section(),
                self.get_feeds_table_area(),
            ],
            className="tabular-main-container",
        )

    def get_feeds_table_area(self):
        return html.Div(
            id="feeds_page_table_area",
            children=[
                dash_table.DataTable(
                    id="feeds_page_table",
                    columns=FEEDS_TABLE_COLS,
                    hidden_columns=[
                        "full_addr",
                        "df_buy_count",
                        "ws_buy_count",
                        "sales",
                    ],
                    row_selectable="single",
                    data=[],
                    sort_action="custom",
                    sort_mode="single",
                ),
                html.Div(
                    id="feeds_page_table_control",
                    children=[
                        table_initial_spinner(),
                    ],
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )
