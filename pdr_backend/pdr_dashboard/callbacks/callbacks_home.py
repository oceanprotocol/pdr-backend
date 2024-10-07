import dash
import polars as pl
from dash import Input, Output, State

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.pdr_dashboard.dash_components.plots import get_figures_and_metrics
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_graph
from pdr_backend.pdr_dashboard.util.format import format_value
from pdr_backend.pdr_dashboard.util.helpers import (
    get_date_period_text_for_selected_predictoors,
    select_or_clear_all_by_table,
)


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
        ],
        [
            State("feeds_table", "data"),
            State("predictoors_table", "selected_rows"),
            State("predictoors_table", "data"),
        ],
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        feeds_table,
        predictoors_table_selected_rows,
        predictoors_table,
    ):
        # feeds_table_selected_rows is a list of ints
        # feeds_data is a list of dicts
        # get the feeds data for the selected rows
        selected_feeds = [feeds_table[i] for i in feeds_table_selected_rows]
        feeds = ArgFeeds.from_table_data(selected_feeds)

        selected_feeds_addrs = [
            feeds_table[i]["contract"] for i in feeds_table_selected_rows
        ]
        selected_predictoors_addrs = [
            predictoors_table[i]["full_addr"] for i in predictoors_table_selected_rows
        ]

        if len(selected_feeds) == 0 or len(selected_predictoors_addrs) == 0:
            payouts = pl.DataFrame()
        else:
            payouts = app.data.payouts_from_bronze_predictions(
                selected_feeds_addrs,
                selected_predictoors_addrs,
            )

        # get figures
        figs_metrics = get_figures_and_metrics(
            payouts,
            feeds,
            selected_predictoors_addrs,
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
        Output("predictoors_table", "selected_rows", allow_duplicate=True),
        [
            Input("search-input-Predictoors", "value"),
            Input("predictoors_table", "selected_rows"),
            Input("show-favourite-addresses", "value"),
            Input("general-lake-date-period-radio-items", "value"),
            Input("predictoor-addrs-local-store", "data"),
        ],
        [State("predictoors_table", "data")],
        prevent_initial_call=True,
    )
    def update_predictoors_table_on_search(
        search_value,
        selected_rows,
        show_favourite_addresses,
        date_period,
        stored_predictoor_addrs,
        predictoors_table,
    ):
        if (
            "general-lake-date-period-radio-items"
            in dash.callback_context.triggered_prop_ids
        ):
            app.data.set_start_date_from_period(date_period)
            app.data.refresh_predictoors_data()
            app.data.refresh_feeds_data()

        formatted_predictoors_data = app.data.formatted_predictoors_home_page_table_data

        selected_predictoors_addrs = [
            predictoors_table[i]["full_addr"] for i in selected_rows
        ]

        if "show-favourite-addresses.value" in dash.callback_context.triggered_prop_ids:
            if stored_predictoor_addrs and len(stored_predictoor_addrs) > 0:
                selected_predictoors_addrs = stored_predictoor_addrs
            else:
                custom_predictoors = formatted_predictoors_data.filter(
                    formatted_predictoors_data["full_addr"].is_in(
                        app.data.favourite_addresses
                    )
                )
                custom_predictoors_addrs = list(custom_predictoors["full_addr"])

                if show_favourite_addresses:
                    selected_predictoors_addrs += custom_predictoors_addrs
                else:
                    selected_predictoors_addrs = [
                        predictoor_addr
                        for predictoor_addr in selected_predictoors_addrs
                        if predictoor_addr not in custom_predictoors_addrs
                    ]

        filtered_data = formatted_predictoors_data.clone()
        if search_value:
            filtered_data = filtered_data.filter(
                filtered_data["full_addr"].str.contains("(?i)" + search_value)
            )

        filtered_data = filtered_data.filter(
            ~filtered_data["full_addr"].is_in(selected_predictoors_addrs)
        )
        selected_predictoors = formatted_predictoors_data.filter(
            formatted_predictoors_data["full_addr"].is_in(selected_predictoors_addrs)
        )

        filtered_data = pl.concat([selected_predictoors, filtered_data])
        selected_predictoor_indices = list(range(len(selected_predictoors)))

        return (filtered_data.to_dicts(), selected_predictoor_indices)

    @app.callback(
        Output("feeds_table", "data"),
        Output("feeds_table", "selected_rows", allow_duplicate=True),
        [
            Input("search-input-Feeds", "value"),
            Input("toggle-switch-predictoor-feeds", "value"),
            Input("predictoors_table", "selected_rows"),
            Input("predictoors_table", "data"),
        ],
        [
            State("feeds_table", "selected_rows"),
            State("feeds_table", "data"),
            State("predictoor-addrs-local-store", "data"),
        ],
        prevent_initial_call=True,
    )
    # pylint: disable=unused-argument
    def update_feeds_table_on_search(
        search_value,
        predictoor_feeds_only,
        predictoors_table_selected_rows,
        predictoors_table,
        selected_rows,
        feeds_table,
        stored_predictoors_addrs,
    ):
        selected_feeds = [feeds_table[i]["contract"] for i in selected_rows]
        # Extract selected predictoor addresses
        predictoors_addrs = [
            predictoors_table[i]["full_addr"] for i in predictoors_table_selected_rows
        ]

        filtered_data = app.data.filter_for_feeds_table(
            predictoor_feeds_only, predictoors_addrs, search_value, selected_feeds
        )

        # if sorted(predictoors_addrs) == sorted(stored_predictoors_addrs)
        # it means we are not on the initial page load, so we use
        # the feeds selected by the user
        if stored_predictoors_addrs and sorted(predictoors_addrs) == sorted(
            stored_predictoors_addrs
        ):
            selected_feeds = list(range(len(filtered_data)))

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

    @app.callback(
        [
            Output("predictoor_config_modal", "is_open"),
            Output("predictoor_addrs", "value"),
        ],
        [
            Input("configure_predictoors", "n_clicks"),
            Input("predictoor-addrs-local-store", "data"),
        ],
        prevent_initial_call=True,
    )
    def open_predictoors_config_modal(n_clicks, predictoor_addrs):
        """
        Select or clear all rows in the feeds table.
        """
        predictoor_addrs_str = "\n".join(predictoor_addrs) if predictoor_addrs else ""

        return (bool(n_clicks > 0), predictoor_addrs_str)

    @app.callback(
        Output("predictoor-addrs-local-store", "data"),
        Input("save_predictoors", "n_clicks"),
        State("predictoor_addrs", "value"),
    )
    def save_predictoors_to_browser_storage(n_clicks, value):
        if not value and not n_clicks:
            return dash.no_update
        addresses = value.split("\n")
        addresses = [
            addr.strip() for addr in addresses if addr.strip()
        ]  # Remove empty lines

        return addresses

    @app.callback(
        Output("show-favourite-addresses", "value"),
        Output("predictoors_table", "selected_rows"),
        Output("feeds_table", "selected_rows"),
        Input("predictoor-addrs-local-store", "data"),
        prevent_initial_call=True,
    )
    def update_show_favourite_check_and_selected_predictoor_rows(
        saved_predictoor_addrs,
    ):
        if not saved_predictoor_addrs and not app.data.favourite_addresses:
            return (False, [], [])

        return (
            True if saved_predictoor_addrs else dash.no_update,
            dash.no_update,
            dash.no_update,
        )
