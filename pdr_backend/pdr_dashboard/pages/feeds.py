from dash import dash_table, dcc, html

from pdr_backend.pdr_dashboard.dash_components.modal import get_modal
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_metric,
    get_search_bar,
)
from pdr_backend.pdr_dashboard.pages.common import Filter, TabularPage, add_to_filter

filters = [
    {"name": "base_token", "placeholder": "Base Token", "options": []},
    {"name": "quote_token", "placeholder": "Quote Token", "options": []},
    {"name": "source", "placeholder": "Source", "options": []},
    {"name": "timeframe", "placeholder": "Timeframe", "options": []},
]

filters_objects = [Filter(**item) for item in filters]


class FeedsPage(TabularPage):
    def __init__(self, app):
        self.app = app

        """
        for feed in app.data.feeds_data:
            pair_base, pair_quote = feed["pair"].split("/")

            # Update base currency filter
            add_to_filter(filters[0]["options"], pair_base)

            # Update quote currency filter
            add_to_filter(filters[1]["options"], pair_quote)

            # Update source filter
            add_to_filter(filters[2]["options"], feed["source"].capitalize())

            # Update timeframe filter
            add_to_filter(filters[3]["options"], feed["timeframe"])
        """

    def layout(self):
        return html.Div(
            [
                dcc.Store(id="user-payout-stats"),
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
                for filter_obj in filters_objects
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
        stats = self.app.data.feeds_metrics

        return html.Div(
            children=[
                get_metric(
                    label=key,
                    value=value,
                    value_id=f"feeds_page_{key}_metric",
                )
                for key, value in stats.items()
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
                #self.get_filters_section(),
                self.get_feeds_table_area(),
            ],
            className="tabular-main-container",
        )

    def get_feeds_table_area(
        self,
    ):
        return html.Div(
            [
                dash_table.DataTable(
                    id="feeds_page_table",
                    #columns=self.app.data.feeds_cols,
                    hidden_columns=["full_addr", "sales_raw"],
                    row_selectable="single",
                    data=self.app.data.feeds_table_data.to_dict('records'),
                    sort_action="custom",
                    sort_mode="single",
                ),
            ],
            style={"width": "100%", "overflow": "scroll"},
        )
