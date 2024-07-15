from dash import Input, Output, State
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
    get_all_payouts_data_from_db,
    filter_objects_by_field,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_graph,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.plots import (
    get_figures,
    process_payouts_for_all_feeds
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
        Output("all-payouts-data", "data"),
        Output("error-message", "children"),
        Input("data-folder", "data"),
    )
    def get_input_data_from_db(files_dir):
        try:
            feeds_data = get_feeds_data_from_db(files_dir)
            predictoors_data = get_predictoors_data_from_db(files_dir)
            all_payots_data = get_all_payouts_data_from_db(files_dir)
            return feeds_data, predictoors_data, all_payots_data, None
        except Exception as e:
            return None, None, dash.html.H3(str(e))

    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("stake_chart", "children"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
        ],
        State("data-folder", "data"),
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        lake_dir,
    ):
        if (
            len(feeds_table_selected_rows) == 0
            or len(predictoors_table_selected_rows) == 0
        ):
            accuracy_fig, profit_fig, stakes_fig = get_figures([], [], [])
            return get_graph(accuracy_fig), get_graph(profit_fig), get_graph(stakes_fig)

        feeds = ArgFeeds.from_table_data(feeds_table_selected_rows)

        predictoors_addrs = [row["user"] for row in predictoors_table_selected_rows]

        payouts = get_payouts_from_db(
            [row["contract"] for row in feeds_table_selected_rows],
            predictoors_addrs,
            lake_dir,
        )

        # get figures
        accuracy_fig, profit_fig, stakes_fig = get_figures(
            payouts,
            feeds,
            predictoors_addrs,
        )

        return get_graph(accuracy_fig), get_graph(profit_fig), get_graph(stakes_fig)

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
            Input("all-payouts-data", "data"),
        ],
    )
    def update_predictoors_table_on_search(
        search_value,
        predictoors_data,
        all_payouts_data
    ):
        """
        Update and filter the predictoors table based on the search input, and
        shorten user addresses for readability regardless of search input.
        
        Args:
            search_value (str): The value entered in the search input.
            predictoors_data (list): The original list of predictoors data.
            all_payouts_data (list): The original list of all payouts data.
        Returns:
            list: The filtered or original predictoors data with shortened user addresses.
        """
        try:
            # Filter predictoors by user address if search value is provided
            if search_value:
                filtered_data = filter_objects_by_field(predictoors_data, "user", search_value)
            else:
                filtered_data = predictoors_data

            # Shorten user addresses for readability
            for row in filtered_data:
                processed_data = []
                if all_payouts_data:
                    processed_data = process_payouts_for_all_feeds(all_payouts_data, row["user"])

                user = row["user"]

                row["total_profit"] = processed_data[4] if processed_data else 0
                row["total_accuracy"] = processed_data[5] if processed_data else 0
                row["avg_stake"] = processed_data[6] if processed_data else 0

                if len(user) > 10:  # Check if the string is long enough to trim
                    row["user"] = f"{user[:5]}...{user[-5:]}"  # Keep the first 5 and last 5 characters

            return filtered_data
        except Exception as e:
            # Log the error or handle it as needed
            print(f"Error updating predictoors table: {e}")
            # Optionally, return an error message or empty data
            return []

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
