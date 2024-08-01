from dash import Input, Output, State


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
        return ""

    @app.callback(
        Output("sales_dropdown", "label"),
        State("sales_min", "value"),
        State("sales_max", "value"),
        Input("sales_button", "n_clicks"),
    )
    def filter_table_by_sales_range(min_val, max_val, btn_clicks):
        if not min_val and not max_val:
            return "Sales"
        """
        Filter table based on selected data ranges.
        """

        return f"Sales {min_val}-{max_val}"

    @app.callback(
        Output("revenue_dropdown", "label"),
        State("revenue_min", "value"),
        State("revenue_max", "value"),
        Input("revenue_button", "n_clicks"),
    )
    def filter_table_by_revenue_range(min_val, max_val, btn_clicks):
        if not min_val and not max_val:
            return "Revenue"
        """
        Filter table based on selected data ranges.
        """

        return f"Revenue {min_val}-{max_val}"

    @app.callback(
        Output("accuracy_dropdown", "label"),
        State("accuracy_min", "value"),
        State("accuracy_max", "value"),
        Input("clear_filters_button", "n_clicks"),
        Input("accuracy_button", "n_clicks"),
    )
    def filter_table_by_accuracy_range(min_val, max_val, btn_clicks, btn_clicks2):
        if not min_val and not max_val:
            return "Accuracy"
        """
        Filter table based on selected data ranges.
        """

        return f"Accuracy {min_val}-{max_val}"

    @app.callback(
        Output("volume_dropdown", "label"),
        State("volume_min", "value"),
        State("volume_max", "value"),
        Input("clear_filters_button", "n_clicks"),
        Input("volume_button", "n_clicks"),
    )
    def filter_table_by_volume_range(min_val, max_val, btn_clicks, btn_clicks2):
        if not min_val and not max_val:
            return "Volume"
        """
        Filter table based on selected data ranges.
        """

        return f"Volume {min_val}-{max_val}"

    @app.callback(
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

        print(btn_clicks)
        return (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        )
