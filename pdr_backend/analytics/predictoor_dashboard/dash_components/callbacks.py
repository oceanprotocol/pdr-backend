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
    get_figures,
)
from pdr_backend.cli.arg_pair import ArgPair


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
        Output("payouts-data", "data"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
            Input("search-input-Feeds", "value"),
            Input("search-input-Predictoors", "value"),
        ],
        State("feeds-data", "data"),
        State("predictoors-data", "data"),
        State("data-folder", "data"),
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        search_value_feeds,
        search_value_predictoors,
        feeds_data,
        predictoors_data,
        lake_dir,
    ):
        feeds_addrs = []
        predictoors_addrs = []
        if (
            len(feeds_table_selected_rows) == 0
            or len(predictoors_table_selected_rows) == 0
        ):
            return dash.no_update

        current_feeds_table_data = update_feeds_table_on_search(
            search_value_feeds, feeds_data
        )
        for i in feeds_table_selected_rows:
            feeds_addrs.append(current_feeds_table_data[i]["contract"])

        current_predictoors_table_data = update_predictoors_table_on_search(
            search_value_predictoors, predictoors_data
        )
        for i in predictoors_table_selected_rows:
            predictoors_addrs.append(current_predictoors_table_data[i]["user"])

        payouts = get_payouts_from_db(feeds_addrs, predictoors_addrs, lake_dir)

        return payouts

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
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("stake_chart", "children"),
        Input("payouts-data", "data"),
        Input("feeds_table", "selected_rows"),
        Input("predictoors_table", "selected_rows"),
        Input("search-input-Feeds", "value"),
        Input("search-input-Predictoors", "value"),
        State("feeds-data", "data"),
        State("predictoors-data", "data"),
    )
    def create_charts(
        payouts_data,
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        search_value_feeds,
        search_value_predictoors,
        feeds_data,
        predictoors_data,
    ):
        feeds_addrs = []
        predictoors_addrs = []

        ## calculate selected feeds
        current_feeds_table_data = update_feeds_table_on_search(
            search_value_feeds, feeds_data
        )
        for i in feeds_table_selected_rows:
            feeds_addrs.append(
                {
                    "contract": current_feeds_table_data[i]["contract"],
                    "feed_name": f"{current_feeds_table_data[i]['pair']}-{current_feeds_table_data[i]['timeframe']}",  # pylint: disable=line-too-long
                }
            )

        ## calculate selected predictoors addrs
        current_predictoors_table_data = update_predictoors_table_on_search(
            search_value_predictoors, predictoors_data
        )
        for i in predictoors_table_selected_rows:
            predictoors_addrs.append(current_predictoors_table_data[i]["user"])

        # get figures
        accuracy_fig, profit_fig, stakes_fig = get_figures(
            payouts_data, feeds_addrs, predictoors_addrs
        )

        return get_graph(accuracy_fig), get_graph(profit_fig), get_graph(stakes_fig)

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
