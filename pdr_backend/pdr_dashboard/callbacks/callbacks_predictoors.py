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


def get_callbacks_predictoors(app):
    @app.callback(
        Output("predictoors_page_table", "data"),
        [
            Input("apy_button", "n_clicks"),
            Input("p_accuracy_button", "n_clicks"),
            Input("gross_income_button", "n_clicks"),
            Input("nr_feeds_button", "n_clicks"),
            Input("stake_button", "n_clicks"),
            Input("costs_button", "n_clicks"),
            Input("search-input-predictoors-table", "value"),
        ],
        State("apy_min", "value"),
        State("apy_max", "value"),
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
        _n_clicks_apy,
        _n_clicks_p_accuracy,
        _n_clicks_gross_income,
        _n_clicks_nr_feeds,
        _n_clicks_stake,
        _n_clicks_costs,
        search_input_value,
        apy_min,
        apy_max,
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
            ("range", "apy", apy_min, apy_max),
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

        return format_table(new_table_data, columns)

    @app.callback(
        Output("apy_dropdown", "label"),
        State("apy_min", "value"),
        State("apy_max", "value"),
        Input("apy_button", "n_clicks"),
        Input("clear_predictoors_filters_button", "n_clicks"),
    )
    def filter_table_by_apy_range(
        min_val, max_val, _n_clicks_apy_btn, _n_clicks_filters_bnt
    ):
        return filter_table_by_range(min_val, max_val, "APY")

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
        Output("apy_min", "value"),
        Output("apy_max", "value"),
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

    # TODO: modals and graph
