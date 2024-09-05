import dash
from dash import Input, Output, State

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.pdr_dashboard.dash_components.plots import get_figures_and_metrics
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_graph
from pdr_backend.pdr_dashboard.util.data import (
    get_date_period_text,
    get_start_date_from_period,
    select_or_clear_all_by_table,
)
from pdr_backend.pdr_dashboard.util.format import format_value


# pylint: disable=too-many-statements
def get_callbacks_home(app):
    @app.callback(
        [
            Output("fig-cache-store", "data"),
            Output("accuracy_chart", "children"),
            Output("profit_chart", "children"),
            Output("cost_chart", "children"),
            Output("stake_chart", "children"),
            Output("accuracy_metric", "children"),
            Output("profit_metric", "children"),
            Output("costs_metric", "children"),
            Output("stake_metric", "children"),
            Output("available_data_period_text", "children"),
        ],
        [
            Input("feeds_table", "selected_rows"),
            Input("date-period-radio-items", "value"),
        ],
        [
            State("feeds_table", "data"),
            State("predictoors_table", "data"),
            State("predictoors_table", "selected_rows"),
            State("fig-cache-store", "data"),
        ],
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        date_period,
        feeds_table,
        predictoors_table,
        predictoors_table_selected_rows,
        cache_store_data,
    ):
        # Create cache key
        selected_feeds = [feeds_table[i] for i in feeds_table_selected_rows]
        selected_predictoors = [
            predictoors_table[i] for i in predictoors_table_selected_rows
        ]
        selected_feeds_contracts = [row["contract"] for row in selected_feeds]
        selected_predictoors_addresses = [row["user"] for row in selected_predictoors]
        cache_key = hash(
            (
                tuple(selected_feeds_contracts),
                tuple(selected_predictoors_addresses),
                date_period,
            )
        )

        # If cache_key is the same as previous cache,
        # return no_update
        # we use str because we had issues
        # with the dcc.Store and int values
        str_cache_key = str(cache_key)
        if cache_store_data == str_cache_key:
            return (dash.no_update,) * 10

        # Update cache store with new cache_key
        feeds = ArgFeeds.from_table_data(selected_feeds)
        predictoors_addrs = [row["user"] for row in selected_predictoors]
        start_date = (
            get_start_date_from_period(int(date_period)) if int(date_period) > 0 else 0
        )
        payouts = app.data.payouts(
            [row["contract"] for row in selected_feeds], predictoors_addrs, start_date
        )

        figs_metrics = get_figures_and_metrics(
            payouts, feeds, predictoors_addrs, app.data.fee_cost
        )
        date_period_text = (
            get_date_period_text(payouts) if int(date_period) == 0 else dash.no_update
        )

        return (
            str_cache_key,
            get_graph(figs_metrics.fig_accuracy),
            get_graph(figs_metrics.fig_profit),
            get_graph(figs_metrics.fig_costs),
            get_graph(figs_metrics.fig_stakes),
            format_value(figs_metrics.avg_accuracy, "accuracy_metric"),
            format_value(figs_metrics.total_profit, "profit_metric"),
            format_value(figs_metrics.total_cost, "costs_metric"),
            format_value(figs_metrics.avg_stake, "stake_metric"),
            date_period_text,
        )

    @app.callback(
        Output("predictoors_table", "data", allow_duplicate=True),
        Output("predictoors_table", "selected_rows", allow_duplicate=True),
        [
            Input("predictoors_table", "data"),
            Input("predictoors_table", "selected_rows"),
        ],
        prevent_initial_call=True,
    )
    def update_predictoors_table_selection(
        predictoors_table,
        selected_rows,
    ):
        selected_table_rows = [predictoors_table[i] for i in selected_rows]
        non_selected_table_rows = [
            row for row in predictoors_table if row not in selected_table_rows
        ]

        return selected_table_rows + non_selected_table_rows, list(
            range(len(selected_table_rows))
        )

    @app.callback(
        Output("predictoors_table", "data", allow_duplicate=True),
        Output("predictoors_table", "selected_rows"),
        [
            Input("search-input-Predictoors", "value"),
            Input("predictoors_table", "data"),
            Input("show-favourite-addresses", "value"),
            Input("predictoors_table", "sort_by"),
        ],
        State("predictoors_table", "selected_rows"),
        prevent_initial_call=True,
    )
    def update_predictoors_table_on_search(
        search_value,
        predictoors_table,
        show_favourite_addresses,
        sort_by,
        selected_rows,
    ):
        selected_predictoors_rows_addresses = [
            predictoors_table[i]["user"] for i in selected_rows
        ]

        show_favourite_addresses = (
            "show-favourite-addresses.value" in dash.callback_context.triggered_prop_ids
        )

        return app.data.filter_for_predictoors_table(
            selected_predictoors_rows_addresses,
            show_favourite_addresses,
            search_value,
            sort_by,
        )

    @app.callback(
        Output("feeds_table", "data", allow_duplicate=True),
        Output("feeds_table", "selected_rows", allow_duplicate=True),
        [
            Input("feeds_table", "data"),
            Input("feeds_table", "selected_rows"),
        ],
        prevent_initial_call=True,
    )
    def update_feeds_table_selection(
        feeds_table,
        selected_rows,
    ):
        selected_table_rows = [feeds_table[i] for i in selected_rows]
        non_selected_table_rows = [
            row for row in feeds_table if row not in selected_table_rows
        ]

        return selected_table_rows + non_selected_table_rows, list(
            range(len(selected_table_rows))
        )

    @app.callback(
        Output("feeds_table", "data", allow_duplicate=True),
        Output("feeds_table", "selected_rows"),
        [
            Input("search-input-Feeds", "value"),
            Input("feeds_table", "data"),
            Input("toggle-switch-predictoor-feeds", "value"),
            Input("predictoors_table", "selected_rows"),
            Input("feeds_table", "sort_by"),
        ],
        State("predictoors_table", "data"),
        State("feeds_table", "selected_rows"),
        prevent_initial_call=True,
    )
    # pylint: disable=unused-argument
    def update_feeds_table_on_search(
        search_value,
        feeds_table,
        predictoor_feeds_only,
        predictoors_table_selected_rows,
        sort_by,
        predictoors_table,
        selected_rows,
    ):
        selected_feeds_addrs = [feeds_table[i]["contract"] for i in selected_rows]
        selected_feeds = [
            f for f in app.data.feeds_data if f["contract"] in selected_feeds_addrs
        ]
        # Extract selected predictoor addresses
        predictoors_addrs = [
            predictoors_table[i]["user"] for i in predictoors_table_selected_rows
        ]

        filtered_data = app.data.filter_for_feeds_table(
            predictoor_feeds_only,
            predictoors_addrs,
            search_value,
            selected_feeds,
            sort_by,
        )

        selected_feed_indices = list(range(len(selected_feeds)))

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
