import dash
from dash import Input, Output, State, callback_context
from pdr_backend.pdr_dashboard.pages.feeds import FeedsPage
from pdr_backend.pdr_dashboard.dash_components.plots import get_feed_figures
from pdr_backend.cli.arg_feeds import ArgFeed


def filter_table_by_range(min_val, max_val, label_text):
    ctx = callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if (not min_val and not max_val) or button_id == "clear_filters_button":
        return label_text

    return f"{label_text} {min_val if min_val else ''}-{max_val if max_val else ''}"


def filter_condition(item, field, values):
    return not values or item[field] in values


def range_condition(item, field, min_value, max_value):
    return not (
        (min_value is not None and min_value != "" and item[field] < min_value)
        or (max_value is not None and max_value != "" and item[field] > max_value)
    )


def check_condition(item, condition_type, field, *values):
    if condition_type == "filter":
        return filter_condition(item, field, values[0])
    if condition_type == "range":
        return range_condition(item, field, values[0], values[1])
    return True


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
        ],
        State("sales_min", "value"),
        State("sales_max", "value"),
        State("revenue_min", "value"),
        State("revenue_max", "value"),
        State("accuracy_min", "value"),
        State("accuracy_max", "value"),
        State("volume_min", "value"),
        State("volume_max", "value"),
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
            ("range", "sales", sales_min, sales_max),
            ("range", "sales_revenue_(OCEAN)", revenue_min, revenue_max),
            ("range", "avg_accuracy", accuracy_min, accuracy_max),
            ("range", "volume_(OCEAN)", volume_min, volume_max),
        ]

        new_table_data = [
            item
            for item in app.feeds_table_data
            if all(check_condition(item, *condition) for condition in conditions)
        ]

        return new_table_data

    @app.callback(
        Output("sales_dropdown", "label"),
        State("sales_min", "value"),
        State("sales_max", "value"),
        Input("sales_button", "n_clicks"),
        Input("clear_filters_button", "n_clicks"),
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
        Input("clear_filters_button", "n_clicks"),
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
        Input("clear_filters_button", "n_clicks"),
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
        Input("clear_filters_button", "n_clicks"),
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
        Input("clear_filters_button", "n_clicks"),
    )
    def clear_all_filters(btn_clicks):
        if not btn_clicks:
            return dash.no_update
        return (
            [],
            [],
            [],
            [],
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )

    @app.callback(
        Output("modal", "is_open"),
        Output("modal", "children"),
        [
            Input("feeds_page_table", "selected_rows"),
        ],
        State("feeds_page_table", "data"),
    )
    def update_graphs(selected_rows, feeds_table_data):
        open_modal = bool(selected_rows)

        if not open_modal:
            return open_modal, []

        selected_row = feeds_table_data[selected_rows[0]]

        feed = ArgFeed(
            selected_row["exchange"].lower(),
            None,
            f'{selected_row["base_token"]}-{selected_row["quote_token"]}',
            selected_row["time"],
            selected_row["full_addr"],
        )

        payouts = app.db_getter.payouts([feed.contract], None, 0)
        subscriptions = app.db_getter.feed_daily_subscriptions_by_feed_id(feed.contract)
        a, b, c, d, e, f = get_feed_figures(payouts, subscriptions)

        feeds_page = FeedsPage(app)
        children = [
            feeds_page.get_feed_graphs_modal_header(selected_row),
            feeds_page.get_feed_graphs_modal_body([a, b, c, d, e, f]),
        ]

        return open_modal, children
