import dash
from dash import Input, Output, State, callback_context


def filter_table_by_range(min_val, max_val, label_text):
    ctx = callback_context
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if (not min_val and not max_val) or button_id == "clear_filters_button":
        return label_text

    return f"{label_text} {min_val}-{max_val}"


def get_callbacks_feeds(app):
    @app.callback(
        [
            Input("base_token", "value"),
            Input("quote_token", "value"),
            Input("venue", "value"),
            Input("time", "value"),
        ]
    )
    def filter_table(base_token, quote_token, venue, time):
        """
        Filter table based on selected dropdown values.
        """

        print(base_token, quote_token, venue, time)
        return dash.no_update

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
