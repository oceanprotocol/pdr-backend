from dash import Input, Output, State
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
    filter_objects_by_field,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_graph,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.plots import (
    get_figures_and_metrics,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    select_or_clear_all_by_table,
)
from pdr_backend.cli.arg_feeds import ArgFeeds


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        Output("feeds-data", "data"),
        Output("predictoors-data", "data"),
        Output("error-message", "children"),
        Input("data-folder", "data"),
    )
    def get_input_data_from_db(files_dir):
        try:
            feeds_data = get_feeds_data_from_db(files_dir)
            predictoors_data = get_predictoors_data_from_db(files_dir)
            return feeds_data, predictoors_data, None
        except Exception as e:
            return None, None, dash.html.H3(str(e))

    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("stake_chart", "children"),
        Output("accuracy_metric", "children"),
        Output("profit_metric", "children"),
        Output("stake_metric", "children"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
            Input("feeds_table", "data"),
            Input("predictoors_table", "data"),
        ],
        State("data-folder", "data"),
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_data,
        predictoors_data,
        lake_dir,
    ):
        # feeds_table_selected_rows is a list of ints
        # feeds_data is a list of dicts
        # get the feeds data for the selected rows
        selected_feeds = [feeds_data[i] for i in feeds_table_selected_rows]
        feeds = ArgFeeds.from_table_data(selected_feeds)

        selected_predictoors = [
            predictoors_data[i] for i in predictoors_table_selected_rows
        ]
        predictoors_addrs = [row["user"] for row in selected_predictoors]

        if len(selected_feeds) == 0 or len(selected_predictoors) == 0:
            payouts = []
        else:
            payouts = get_payouts_from_db(
                [row["contract"] for row in selected_feeds],
                predictoors_addrs,
                lake_dir,
            )

        # get figures
        accuracy_fig, profit_fig, stakes_fig, avg_accuracy, total_profit, avg_stake = (
            get_figures_and_metrics(
                payouts,
                feeds,
                predictoors_addrs,
            )
        )

        return (
            get_graph(accuracy_fig),
            get_graph(profit_fig),
            get_graph(stakes_fig),
            f"{round(avg_accuracy, 2)}%",
            f"{round(total_profit, 2)} OCEAN",
            f"{round(avg_stake, 2)} OCEAN",
        )

    @app.callback(
        Output("feeds_table", "columns"),
        Input("feeds-data", "data"),
    )
    def create_feeds_table(feeds_data):
        if not feeds_data:
            return dash.no_update

        for feed in feeds_data:
            del feed["contract"]

        columns = [{"name": col, "id": col} for col in feeds_data[0].keys()]
        return columns

    @app.callback(
        Output("predictoors_table", "columns"),
        Input("predictoors-data", "data"),
    )
    def create_predictoors_table(predictoors_data):
        if not predictoors_data:
            return dash.no_update
        columns = [{"name": col, "id": col} for col in predictoors_data[0].keys()]
        return columns

    @app.callback(
        Output("predictoors_table", "data"),
        [
            Input("search-input-Predictoors", "value"),
            Input("predictoors-data", "data"),
        ],
    )
    def update_predictoors_table_on_search(search_value, predictoors_data):
        if not search_value:
            return predictoors_data

        # filter predictoors by user address
        filtered_data = filter_objects_by_field(predictoors_data, "user", search_value)
        return filtered_data

    @app.callback(
        Output("feeds_table", "data"),
        [
            Input("search-input-Feeds", "value"),
            Input("feeds-data", "data"),
        ],
    )
    def update_feeds_table_on_search(search_value, feeds_data):
        if not search_value:
            return feeds_data

        # filter feeds by pair address
        filtered_data = filter_objects_by_field(feeds_data, "pair", search_value)
        return filtered_data

    @app.callback(
        Output("feeds_table", "selected_rows"),
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
        Output("predictoors_table", "selected_rows"),
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
