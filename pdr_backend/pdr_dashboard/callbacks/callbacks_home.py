import dash
from dash import Input, Output, State

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.pdr_dashboard.dash_components.plots import get_figures_and_metrics
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_graph
from pdr_backend.pdr_dashboard.util.data import (
    filter_objects_by_field,
    get_date_period_text_for_selected_predictoors,
    select_or_clear_all_by_table,
)
from pdr_backend.pdr_dashboard.util.format import format_value


# pylint: disable=too-many-statements
def get_callbacks_home(app):
    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("cost_chart", "children"),
        Output("stake_chart", "children"),
        Output("accuracy_metric", "children"),
        Output("profit_metric", "children"),
        Output("costs_metric", "children"),
        Output("stake_metric", "children"),
        Output("available_data_period_text", "children"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
            Input("feeds_table", "data"),
            Input("predictoors_table", "data"),
            Input("general-lake-date-period-radio-items", "value"),
        ],
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_table,
        predictoors_table,
        _date_period,
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
            payouts = app.data.payouts(
                [row["contract"] for row in selected_feeds],
                predictoors_addrs,
                0,
            )

        # get figures
        figs_metrics = get_figures_and_metrics(
            payouts,
            feeds,
            predictoors_addrs,
            app.data.fee_cost,
        )

        # get available period date text
        date_period_text = get_date_period_text_for_selected_predictoors(payouts)

        return (
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
        Output("predictoors_table", "selected_rows"),
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
        formatted_predictoors_data = app.data.formatted_predictoors_home_page_table_data
        selected_predictoors = [predictoors_table[i] for i in selected_rows]
        filtered_data = formatted_predictoors_data

        if "show-favourite-addresses.value" in dash.callback_context.triggered_prop_ids:
            custom_predictoors = [
                predictoor
                for predictoor in formatted_predictoors_data
                if predictoor["user"] in app.data.favourite_addresses
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
        else:
            filtered_data = [p for p in filtered_data if p not in selected_predictoors]

        filtered_data = selected_predictoors + filtered_data
        selected_predictoor_indices = list(range(len(selected_predictoors)))

        return (filtered_data, selected_predictoor_indices)

    @app.callback(
        Output("feeds_table", "data"),
        Output("feeds_table", "selected_rows"),
        [
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

        filtered_data = app.data.filter_for_feeds_table(
            predictoor_feeds_only, predictoors_addrs, search_value, selected_feeds
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
