from dash import dash_table, html

from pdr_backend.pdr_dashboard.dash_components.modal import get_modal
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_search_bar,
)
from pdr_backend.pdr_dashboard.pages.common import TabularPage


class PredictoorsPage(TabularPage):
    def __init__(self, app):
        self.app = app
        self.app.data.get_predictoors_data()

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
        return html.Div(
            children=[
                get_metric(
                    label=key,
                    value=value,
                    value_id=key_id_name(key),
                )
                for key, value in self.app.data.predictoors_metrics_data.items()
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
        return html.Div(
            [
                self.get_filters_section(),
                self.get_predictoor_table_area(),
            ],
            className="tabular-main-container",
        )

    def get_predictoor_table_area(self):
        return html.Div(
            [
                dash_table.DataTable(
                    id="predictoors_page_table",
                    columns=self.app.data.predictoors_cols,
                    hidden_columns=["full_addr"],
                    row_selectable="single",
                    data=self.app.data.predictoors_table_data,
                    sort_action="custom",
                    sort_mode="single",
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )


def key_id_name(key: str) -> str:
    sanitized_key = key.lower().replace(" ", "_").replace("(avg)", "")

    return f"predictoors_page_{sanitized_key}_metric"
