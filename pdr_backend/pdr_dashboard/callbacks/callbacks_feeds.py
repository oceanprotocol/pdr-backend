import dash
from dash import Input, Output, State

from pdr_backend.pdr_dashboard.pages.feeds import get_metric
from pdr_backend.pdr_dashboard.util.data import (
    get_feed_column_ids,
)
from pdr_backend.pdr_dashboard.dash_components.modal import ModalContent
from pdr_backend.pdr_dashboard.util.filters import (
    check_condition,
    filter_table_by_range,
)
from pdr_backend.pdr_dashboard.util.format import format_table
from pdr_backend.pdr_dashboard.util.helpers import toggle_modal_helper


def get_callbacks_feeds(app):
    @app.callback(
        Output("feeds_page_table", "data", allow_duplicate=True),
        Output("feeds_page_metrics_row", "children"),
        [Input("start-date", "data")],
        prevent_initial_call=True,
    )
    def update_page_data(start_date):
        app.data.get_feeds_data(start_date)

        metrics_children_data = [
            get_metric(
                label=key,
                value=value,
                value_id=f"feeds_page_{key}_metric",
            )
            for key, value in app.data.feeds_metrics_data.items()
        ]

        return app.data.feeds_table_data, metrics_children_data

    @app.callback(
        Output("feeds_page_table", "data"),
        [
            Input("base_token", "value"),
            Input("quote_token", "value"),
            Input("source", "value"),
            Input("timeframe", "value"),
            Input("sales_button", "n_clicks"),
            Input("revenue_button", "n_clicks"),
            Input("accuracy_button", "n_clicks"),
            Input("volume_button", "n_clicks"),
            Input("search-input-feeds-table", "value"),
            Input("feeds_page_table", "sort_by"),
        ],
        State("sales_min", "value"),
        State("sales_max", "value"),
        State("revenue_min", "value"),
        State("revenue_max", "value"),
        State("accuracy_min", "value"),
        State("accuracy_max", "value"),
        State("volume_min", "value"),
        State("volume_max", "value"),
        prevent_initial_call=True,
    )
    def filter_table(
        base_token,
        quote_token,
        source,
        timeframe,
        _n_clicks_sales,
        _n_clicks_revenue,
        _n_clicks_accuracy,
        _n_clicks_volume,
        search_input_value,
        sort_by,
        sales_min,
        sales_max,
        revenue_min,
        revenue_max,
        accuracy_min,
        accuracy_max,
        volume_min,
        volume_max,
    ):
        """
        Filter table based on selected dropdown values.
        """

        conditions = [
            ("filter", "base_token", base_token),
            ("filter", "quote_token", quote_token),
            ("filter", "source", source),
            ("filter", "timeframe", timeframe),
            ("range", "sales_raw", sales_min, sales_max),
            ("range", "sales_revenue_(OCEAN)", revenue_min, revenue_max),
            ("range", "avg_accuracy", accuracy_min, accuracy_max),
            ("range", "volume_(OCEAN)", volume_min, volume_max),
            ("search", None, search_input_value),
        ]

        new_table_data = [
            item
            for item in app.data.raw_feeds_data
            if all(check_condition(item, *condition) for condition in conditions)
        ]

        columns = []
        if new_table_data:
            columns = get_feed_column_ids(new_table_data[0])

        if sort_by:
            # Extract sort criteria
            sort_col = sort_by[0]["column_id"]
            ascending = sort_by[0]["direction"] == "asc"

            # Sort by raw "Price" even if the "Formatted Price" is displayed
            new_table_data = sorted(
                new_table_data, key=lambda x: x[sort_col], reverse=not ascending
            )

        return format_table(new_table_data, columns)

    @app.callback(
        Output("sales_dropdown", "label"),
        State("sales_min", "value"),
        State("sales_max", "value"),
        Input("sales_button", "n_clicks"),
        Input("clear_feeds_filters_button", "n_clicks"),
    )
    def filter_table_by_sales_range(
        min_val, max_val, _n_clicks_sales_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Sales")

    @app.callback(
        Output("revenue_dropdown", "label"),
        State("revenue_min", "value"),
        State("revenue_max", "value"),
        Input("revenue_button", "n_clicks"),
        Input("clear_feeds_filters_button", "n_clicks"),
    )
    def filter_table_by_revenue_range(
        min_val, max_val, _n_clicks_revenue_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Revenue")

    @app.callback(
        Output("accuracy_dropdown", "label"),
        State("accuracy_min", "value"),
        State("accuracy_max", "value"),
        Input("accuracy_button", "n_clicks"),
        Input("clear_feeds_filters_button", "n_clicks"),
    )
    def filter_table_by_accuracy_range(
        min_val, max_val, _n_clicks_accuracy_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Accuracy")

    @app.callback(
        Output("volume_dropdown", "label"),
        State("volume_min", "value"),
        State("volume_max", "value"),
        Input("volume_button", "n_clicks"),
        Input("clear_feeds_filters_button", "n_clicks"),
    )
    def filter_table_by_volume_range(
        min_val, max_val, _n_clicks_volume_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Volume")

    @app.callback(
        Output("base_token", "value"),
        Output("quote_token", "value"),
        Output("source", "value"),
        Output("timeframe", "value"),
        Output("sales_min", "value"),
        Output("sales_max", "value"),
        Output("revenue_min", "value"),
        Output("revenue_max", "value"),
        Output("accuracy_min", "value"),
        Output("accuracy_max", "value"),
        Output("volume_min", "value"),
        Output("volume_max", "value"),
        Output("search-input-feeds-table", "value"),
        Input("clear_feeds_filters_button", "n_clicks"),
    )
    def clear_all_filters(btn_clicks):
        if not btn_clicks:
            return dash.no_update
        return ([], [], [], [], None, None, None, None, None, None, None, None, "")

    @app.callback(
        Output("feeds_modal", "is_open"),
        Output("feeds_page_table", "selected_rows"),
        [Input("feeds_page_table", "selected_rows"), Input("feeds_modal", "is_open")],
    )
    def toggle_modal(selected_rows, is_open_input):
        ctx = dash.callback_context
        return toggle_modal_helper(
            ctx,
            selected_rows,
            is_open_input,
            "feeds_modal",
        )

    @app.callback(
        Output("feeds_modal", "children"),
        Input("feeds_modal", "is_open"),
        State("feeds_page_table", "selected_rows"),
        State("feeds_page_table", "data"),
    )
    # pylint: disable=unused-argument
    def update_graphs(is_open, selected_rows, feeds_table_data):
        content = ModalContent("feeds_modal", app.data)
        content.selected_row = (
            feeds_table_data[selected_rows[0]] if selected_rows else None
        )

        return content.get_content()
