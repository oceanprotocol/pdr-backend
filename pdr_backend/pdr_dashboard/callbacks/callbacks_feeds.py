import dash
from dash import Input, Output, State, callback_context


def filter_table_by_range(min_val, max_val, label_text):
    ctx = callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if (not min_val and not max_val) or button_id == "clear_filters_button":
        return label_text

    return f"{label_text} {min_val if min_val else ''}-{max_val if max_val else ''}"


def filter_condition(item, field, values):
    if not values:
        return True
    return item[field] in values


def range_condition(item, field, min_value, max_value):
    if min_value is not None and min_value is not "" and item[field] < min_value:
        return False
    if max_value is not None and min_value is not "" and item[field] > max_value:
        return False
    return True


def get_callbacks_feeds(app):
    @app.callback(
        Output("feeds_page_table", "data"),
        [
            Input("base_token", "value"),
            Input("quote_token", "value"),
            Input("venue", "value"),
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
        venue,
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

        new_table_data = [
            item
            for item in app.feeds_table_data
            if filter_condition(item, "base_token", base_token)
            and filter_condition(item, "quote_token", quote_token)
            and filter_condition(item, "venue", venue)
            and filter_condition(item, "time", time)
            and range_condition(item, "sales", sales_min, sales_max)
            and range_condition(item, "sales_revenue_(OCEAN)", revenue_min, revenue_max)
            and range_condition(item, "avg_accuracy", accuracy_min, accuracy_max)
            and range_condition(item, "volume_(OCEAN)", volume_min, volume_max)
        ]

        return new_table_data

    @app.callback(
        Output("sales_dropdown", "label"),
        State("sales_min", "value"),
        State("sales_max", "value"),
        Input("sales_button", "n_clicks"),
        Input("clear_filters_button", "n_clicks"),
    )
    def filter_table_by_sales_range(min_val, max_val, _btn_1, _bnt_2):
        return filter_table_by_range(min_val, max_val, "Sales")

    @app.callback(
        Output("revenue_dropdown", "label"),
        State("revenue_min", "value"),
        State("revenue_max", "value"),
        Input("revenue_button", "n_clicks"),
        Input("clear_filters_button", "n_clicks"),
    )
    def filter_table_by_revenue_range(min_val, max_val, _btn_1, _bnt_2):
        return filter_table_by_range(min_val, max_val, "Revenue")

    @app.callback(
        Output("accuracy_dropdown", "label"),
        State("accuracy_min", "value"),
        State("accuracy_max", "value"),
        Input("clear_filters_button", "n_clicks"),
        Input("accuracy_button", "n_clicks"),
    )
    def filter_table_by_accuracy_range(min_val, max_val, _btn_1, _bnt_2):
        return filter_table_by_range(min_val, max_val, "Accuracy")

    @app.callback(
        Output("volume_dropdown", "label"),
        State("volume_min", "value"),
        State("volume_max", "value"),
        Input("clear_filters_button", "n_clicks"),
        Input("volume_button", "n_clicks"),
    )
    def filter_table_by_volume_range(min_val, max_val, _btn_1, _bnt_2):
        return filter_table_by_range(min_val, max_val, "Volume")

    @app.callback(
        Output("base_token", "value"),
        Output("quote_token", "value"),
        Output("venue", "value"),
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
