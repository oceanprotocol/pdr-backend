import dash
from dash import Input, Output, State

from pdr_backend.pdr_dashboard.dash_components.modal import ModalContent
from pdr_backend.pdr_dashboard.util.data import get_feed_column_ids
from pdr_backend.pdr_dashboard.util.filters import (
    check_condition,
    filter_table_by_range,
)
from pdr_backend.pdr_dashboard.util.format import format_table
from pdr_backend.pdr_dashboard.util.helpers import toggle_modal_helper


def get_callbacks_predictoors(app):
    @app.callback(
        Output("predictoors_page_table", "data"),
        [
            Input("apr_button", "n_clicks"),
            Input("p_accuracy_button", "n_clicks"),
            Input("gross_income_button", "n_clicks"),
            Input("nr_feeds_button", "n_clicks"),
            Input("stake_button", "n_clicks"),
            Input("costs_button", "n_clicks"),
            Input("search-input-predictoors-table", "value"),
            Input("predictoors_page_table", "sort_by"),
        ],
        State("apr_min", "value"),
        State("apr_max", "value"),
        State("p_accuracy_min", "value"),
        State("p_accuracy_max", "value"),
        State("gross_income_min", "value"),
        State("gross_income_max", "value"),
        State("nr_feeds_min", "value"),
        State("nr_feeds_max", "value"),
        State("stake_min", "value"),
        State("stake_max", "value"),
        State("costs_min", "value"),
        State("costs_max", "value"),
        prevent_initial_call=True,
    )
    def filter_table(
        _n_clicks_apr,
        _n_clicks_p_accuracy,
        _n_clicks_gross_income,
        _n_clicks_nr_feeds,
        _n_clicks_stake,
        _n_clicks_costs,
        search_input_value,
        sort_by,
        apr_min,
        apr_max,
        p_accuracy_min,
        p_accuracy_max,
        gross_income_min,
        gross_income_max,
        nr_feeds_min,
        nr_feeds_max,
        stake_min,
        stake_max,
        costs_min,
        costs_max,
    ):
        """
        Filter table based on selected dropdown values.
        """

        conditions = [
            ("range", "apr", apr_min, apr_max),
            ("range", "p_accuracy", p_accuracy_min, p_accuracy_max),
            ("range", "gross_income_(OCEAN)", gross_income_min, gross_income_max),
            ("range", "number_of_feeds", nr_feeds_min, nr_feeds_max),
            ("range", "staked_(OCEAN)", stake_min, stake_max),
            ("range", "tx_costs_(OCEAN)", costs_min, costs_max),
            ("search", None, search_input_value),
        ]

        new_table_data = [
            item
            for item in app.predictoor_table_data
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
        Output("apr_dropdown", "label"),
        State("apr_min", "value"),
        State("apr_max", "value"),
        Input("apr_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_apr_range(
        min_val, max_val, _n_clicks_apr_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "APR")

    @app.callback(
        Output("p_accuracy_dropdown", "label"),
        State("p_accuracy_min", "value"),
        State("p_accuracy_max", "value"),
        Input("p_accuracy_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_p_accuracy_range(
        min_val, max_val, _n_clicks_p_accuracy_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Accuracy")

    @app.callback(
        Output("gross_income_dropdown", "label"),
        State("gross_income_min", "value"),
        State("gross_income_max", "value"),
        Input("gross_income_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_gross_income_range(
        min_val, max_val, _n_clicks_gross_income_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Gross Income")

    @app.callback(
        Output("nr_feeds_dropdown", "label"),
        State("nr_feeds_min", "value"),
        State("nr_feeds_max", "value"),
        Input("nr_feeds_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_nr_feeds_range(
        min_val, max_val, _n_clicks_nr_feeds_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Nr Feeds")

    @app.callback(
        Output("stake_dropdown", "label"),
        State("stake_min", "value"),
        State("stake_max", "value"),
        Input("stake_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_stake_range(
        min_val, max_val, _n_clicks_stake_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Stake")

    @app.callback(
        Output("costs_dropdown", "label"),
        State("costs_min", "value"),
        State("costs_max", "value"),
        Input("costs_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_costs_range(
        min_val, max_val, _n_clicks_costs_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "Costs")

    @app.callback(
        Output("apr_min", "value"),
        Output("apr_max", "value"),
        Output("p_accuracy_min", "value"),
        Output("p_accuracy_max", "value"),
        Output("gross_income_min", "value"),
        Output("gross_income_max", "value"),
        Output("nr_feeds_min", "value"),
        Output("nr_feeds_max", "value"),
        Output("stake_min", "value"),
        Output("stake_max", "value"),
        Output("costs_min", "value"),
        Output("costs_max", "value"),
        Output("search-input-predictoors-table", "value"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def clear_all_filters(btn_clicks):
        if not btn_clicks:
            return dash.no_update

        return (
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "",
        )

    @app.callback(
        Output("predictoors_modal", "is_open"),
        Output("predictoors_page_table", "selected_rows"),
        [
            Input("predictoors_page_table", "selected_rows"),
            Input("predictoors_modal", "is_open"),
        ],
    )
    def toggle_modal(selected_rows, is_open_input):
        ctx = dash.callback_context
        return toggle_modal_helper(
            ctx,
            selected_rows,
            is_open_input,
            "predictoors_modal",
        )

    @app.callback(
        Output("predictoors_modal", "children"),
        Input("predictoors_modal", "is_open"),
        State("predictoors_page_table", "selected_rows"),
        State("predictoors_page_table", "data"),
    )
    # pylint: disable=unused-argument
    def update_graphs(is_open, selected_rows, predictoors_table_data):
        content = ModalContent("predictoors_modal", app.db_getter)
        content.selected_row = (
            predictoors_table_data[selected_rows[0]] if selected_rows else None
        )

        return content.get_content()
