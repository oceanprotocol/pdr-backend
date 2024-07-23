import copy

import dash

from dash import Input, Output, State

from pdr_backend.pdr_dashboard.dash_components.app_constants import (
    PREDICTOOR_TABLE_COLUMNS,
    PREDICTOOR_TABLE_HIDDEN_COLUMNS,
)
from pdr_backend.pdr_dashboard.dash_components.plots import (
    get_figures_and_metrics,
)

from pdr_backend.pdr_dashboard.dash_components.util import (
    filter_objects_by_field,
    get_date_period_text,
    get_feed_ids_based_on_predictoors_from_db,
    get_payouts_from_db,
    get_start_date_from_period,
    select_or_clear_all_by_table,
    calculate_gass_fee_costs,
)
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_graph,
)

from pdr_backend.cli.arg_feeds import ArgFeeds


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        [
            Output("show-favourite-addresses", "value"),
            Output("is-loading", "value"),
        ],
        Input("is-loading", "value"),
    )
    # pylint: disable=unused-argument
    def startup(is_loading):
        show_favourite_addresses = True if app.favourite_addresses else []
        return show_favourite_addresses, 0

    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("cost_chart", "children"),
        Output("stake_chart", "children"),
        Output("accuracy_metric", "children"),
        Output("profit_metric", "children"),
        Output("stake_metric", "children"),
        Output("available_data_period_text", "children"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
            Input("feeds_table", "data"),
            Input("predictoors_table", "data"),
            Input("date-period-radio-items", "value"),
        ],
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_table,
        predictoors_table,
        date_period,
    ):
        # feeds_table_selected_rows is a list of ints
        # feeds_data is a list of dicts
        # get the feeds data for the selected rows
        selected_feeds = [feeds_table[i] for i in feeds_table_selected_rows]
        feeds = ArgFeeds.from_table_data(selected_feeds)

        selected_predictoors = [
            predictoors_table[i] for i in predictoors_table_selected_rows
        ]
        predictoors_addrs = [row["user"] for row in selected_predictoors]

        if len(selected_feeds) == 0 or len(selected_predictoors) == 0:
            payouts = []
        else:
            start_date = (
                get_start_date_from_period(int(date_period))
                if int(date_period) > 0
                else 0
            )
            payouts = get_payouts_from_db(
                [row["contract"] for row in selected_feeds],
                predictoors_addrs,
                start_date,
                app.lake_dir,
            )

        # get fee estimate
        fee_cost = calculate_gass_fee_costs(app.web3_pp, feeds[0].contract, app.prices)

        # get figures
        (
            accuracy_fig,
            profit_fig,
            costs_fig,
            stakes_fig,
            avg_accuracy,
            total_profit,
            avg_stake,
        ) = get_figures_and_metrics(payouts, feeds, predictoors_addrs, fee_cost)

        # get available period date text
        date_period_text = (
            get_date_period_text(payouts)
            if (
                int(date_period) == 0
                and (len(selected_feeds) > 0 or len(selected_predictoors) > 0)
            )
            else dash.no_update
        )

        return (
            get_graph(accuracy_fig),
            get_graph(profit_fig),
            get_graph(costs_fig),
            get_graph(stakes_fig),
            f"{round(avg_accuracy, 2)}%",
            f"{round(total_profit, 2)} OCEAN",
            f"{round(avg_stake, 2)} OCEAN",
            date_period_text,
        )

    @app.callback(
        Output("feeds_table", "columns"),
        Output("feeds_table", "data"),
        Input("is-loading", "value"),
    )
    # pylint: disable=unused-argument
    def create_feeds_table(is_loading):
        if not app.feeds_data:
            return dash.no_update

        data = copy.deepcopy(app.feeds_data)
        for feed in data:
            del feed["contract"]

        columns = [{"name": col, "id": col} for col in data[0].keys()]
        return columns, data

    @app.callback(
        Output("predictoors_table", "columns"),
        Output("predictoors_table", "data"),
        Input("is-loading", "value"),
    )
    # pylint: disable=unused-argument
    def create_predictoors_table(is_loading):
        if not app.predictoors_data:
            return dash.no_update
        columns = [{"name": col, "id": col} for col in app.predictoors_data[0].keys()]

        return columns, app.predictoors_data

    @app.callback(
        Output("predictoors_table", "data", allow_duplicate=True),
        Output("predictoors_table", "selected_rows"),
        Output("predictoors_table", "columns", allow_duplicate=True),
        Output("predictoors_table", "hidden_columns"),
        [
            Input("search-input-Predictoors", "value"),
            Input("predictoors_table", "selected_rows"),
            Input("predictoors_table", "data"),
            Input("show-favourite-addresses", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_predictoors_table_on_search(
        search_value,
        selected_rows,
        predictoors_table,
        show_favourite_addresses,
    ):
        selected_predictoors = [predictoors_table[i] for i in selected_rows]
        filtered_data = app.predictoors_data

        if "show-favourite-addresses.value" in dash.callback_context.triggered_prop_ids:
            custom_predictoors = [
                predictoor
                for predictoor in app.predictoors_data
                if predictoor["user"] in app.favourite_addresses
            ]

            if show_favourite_addresses:
                selected_predictoors += custom_predictoors
            else:
                selected_predictoors = [
                    predictoor
                    for predictoor in selected_predictoors
                    if predictoor not in custom_predictoors
                ]

        if search_value:
            # filter predictoors by user address
            filtered_data = filter_objects_by_field(
                filtered_data, "user", search_value, selected_predictoors
            )

        selected_predictoor_indices = [
            i
            for i, predictoor in enumerate(filtered_data)
            if predictoor in selected_predictoors
        ]

        return (
            filtered_data,
            selected_predictoor_indices,
            PREDICTOOR_TABLE_COLUMNS,
            PREDICTOOR_TABLE_HIDDEN_COLUMNS,
        )

    @app.callback(
        Output("feeds_table", "data", allow_duplicate=True),
        Output("feeds_table", "selected_rows"),
        [
            Input("is-loading", "value"),
            Input("search-input-Feeds", "value"),
            Input("feeds_table", "selected_rows"),
            Input("feeds_table", "data"),
            Input("toggle-switch-predictoor-feeds", "value"),
            Input("predictoors_table", "selected_rows"),
        ],
        State("predictoors_table", "data"),
        prevent_initial_call=True,
    )
    # pylint: disable=unused-argument
    def update_feeds_table_on_search(
        is_loading,
        search_value,
        selected_rows,
        feeds_table,
        predictoor_feeds_only,
        predictoors_table_selected_rows,
        predictoors_table,
    ):
        selected_feeds = [feeds_table[i] for i in selected_rows]
        # Extract selected predictoor addresses
        predictoors_addrs = [
            predictoors_table[i]["user"] for i in predictoors_table_selected_rows
        ]

        # filter feeds by pair address
        filtered_data = (
            filter_objects_by_field(
                app.feeds_data, "pair", search_value, selected_feeds
            )
            if search_value
            else app.feeds_data
        )

        # filter feeds by payouts from selected predictoors
        if predictoor_feeds_only and (len(predictoors_addrs) > 0):
            feed_ids = get_feed_ids_based_on_predictoors_from_db(
                app.lake_dir,
                predictoors_addrs,
            )
            filtered_data = [
                obj for obj in app.feeds_data if obj["contract"] in feed_ids
            ]

        if (
            app.favourite_addresses
            and "is-loading.value" in dash.callback_context.triggered_prop_ids
        ):
            return filtered_data, list(range(len(filtered_data)))

        selected_feed_indices = [
            i for i, feed in enumerate(filtered_data) if feed in selected_feeds
        ]

        return filtered_data, selected_feed_indices

    @app.callback(
        Output("feeds_table", "selected_rows", allow_duplicate=True),
        [
            Input("select-all-feeds_table", "n_clicks"),
            Input("clear-all-feeds_table", "n_clicks"),
        ],
        State("feeds_table", "data"),
        prevent_initial_call=True,
    )
    def select_or_clear_all_feeds(_, __, rows):
        """
        Select or clear all rows in the feeds table.
        """

        ctx = dash.callback_context
        return select_or_clear_all_by_table(ctx, "feeds_table", rows)

    @app.callback(
        Output("predictoors_table", "selected_rows", allow_duplicate=True),
        [
            Input("select-all-predictoors_table", "n_clicks"),
            Input("clear-all-predictoors_table", "n_clicks"),
        ],
        State("predictoors_table", "data"),
        prevent_initial_call=True,
    )
    def select_or_clear_all_predictoors(_, __, rows):
        """
        Select or clear all rows in the predictoors table.
        """

        ctx = dash.callback_context
        return select_or_clear_all_by_table(ctx, "predictoors_table", rows)
