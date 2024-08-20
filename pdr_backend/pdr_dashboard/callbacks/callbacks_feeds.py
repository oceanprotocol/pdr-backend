import dash
from dash import Input, Output, State

from pdr_backend.cli.arg_feeds import ArgFeed
from pdr_backend.pdr_dashboard.dash_components.plots import (
    FeedModalFigures,
    get_feed_figures,
)
from pdr_backend.pdr_dashboard.pages.feeds import FeedsPage
from pdr_backend.pdr_dashboard.util.data import get_feed_column_ids
from pdr_backend.pdr_dashboard.util.format import format_table
from pdr_backend.pdr_dashboard.util.filters import (
    filter_table_by_range,
    check_condition,
)


def get_callbacks_feeds(app):
    @app.callback(
        Output("feeds_page_table", "data"),
        [
            Input("base_token", "value"),
            Input("quote_token", "value"),
            Input("exchange", "value"),
            Input("time", "value"),
            Input("sales_button", "n_clicks"),
            Input("revenue_button", "n_clicks"),
            Input("accuracy_button", "n_clicks"),
            Input("volume_button", "n_clicks"),
            Input("search-input-feeds-table", "value"),
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
        exchange,
        time,
        _n_clicks_sales,
        _n_clicks_revenue,
        _n_clicks_accuracy,
        _n_clicks_volume,
        search_input_value,
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
            ("filter", "exchange", exchange),
            ("filter", "time", time),
            ("range", "sales_raw", sales_min, sales_max),
            ("range", "sales_revenue_(OCEAN)", revenue_min, revenue_max),
            ("range", "avg_accuracy", accuracy_min, accuracy_max),
            ("range", "volume_(OCEAN)", volume_min, volume_max),
            ("search", None, search_input_value),
        ]

        new_table_data = [
            item
            for item in app.feeds_table_data
            if all(check_condition(item, *condition) for condition in conditions)
        ]

        columns = []
        if new_table_data:
            columns = get_feed_column_ids(new_table_data[0])

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
        Output("exchange", "value"),
        Output("time", "value"),
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
        Output("modal", "is_open"),
        Output("feeds_page_table", "selected_rows"),
        [Input("feeds_page_table", "selected_rows"), Input("modal", "is_open")],
    )
    def toggle_modal(selected_rows, is_open_input):
        ctx = dash.callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id not in ["feeds_page_table", "modal"]:
            return dash.no_update, dash.no_update

        if triggered_id == "modal":
            if is_open_input:
                return dash.no_update, dash.no_update

            # Modal close button is clicked, clear the selection
            return False, []

        # triggered_id == "feeds_page_table"
        if selected_rows and not is_open_input:
            return True, dash.no_update

        # Clear the selection if modal is not opened
        return False, []

    @app.callback(
        Output("modal", "children"),
        Input("modal", "is_open"),
        State("feeds_page_table", "selected_rows"),
        State("feeds_page_table", "data"),
    )
    def update_graphs(is_open, selected_rows, feeds_table_data):
        feeds_page = FeedsPage(app)
        if not is_open or not selected_rows:
            return feeds_page.get_default_modal_content()

        selected_row = feeds_table_data[selected_rows[0]]

        feed = ArgFeed(
            exchange=selected_row["exchange"].lower(),
            signal=None,
            pair=f'{selected_row["base_token"]}-{selected_row["quote_token"]}',
            timeframe=selected_row["time"],
            contract=selected_row["full_addr"],
        )

        payouts = app.db_getter.payouts([feed.contract], None, 0)
        subscriptions = app.db_getter.feed_daily_subscriptions_by_feed_id(feed.contract)
        feed_figures: FeedModalFigures = get_feed_figures(payouts, subscriptions)

        children = [
            feeds_page.get_feed_graphs_modal_header(selected_row),
            feeds_page.get_feed_graphs_modal_body(feed_figures.get_figures()),
        ]

        return children
