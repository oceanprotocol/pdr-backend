from dash import Input, Output
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


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        Output("feeds-data", "data"),
        Output("predictoors-data", "data"),
        Output("error-message", "children"),
        Input("loading", "children"),
    )
    # Dash runs all callbacks at app startup
    # but it also requires at least an Input, so we use a dummy Input
    def get_input_data_from_db(noop):  # pylint: disable=unused-argument
        try:
            feeds_data = get_feeds_data_from_db(app.lake_dir)
            predictoors_data = get_predictoors_data_from_db(app.lake_dir)
            return feeds_data, predictoors_data, None
        except Exception as e:
            return None, None, dash.html.H3(str(e))

    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Output("stake_chart", "children"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
            Input("feeds_table", "data"),
            Input("predictoors_table", "data"),
        ],
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_data,
        predictoors_data,
    ):
        feeds_display_data = []
        predictoors_addrs = []

        selected_feeds = [feeds_data[i] for i in feeds_table_selected_rows]

        # calculate selected feeds
        for row in selected_feeds:
            feeds_display_data.append(
                {
                    "contract": row["contract"],
                    "feed_name": f"{row['pair']}-{row['timeframe']}",  # pylint: disable=line-too-long
                }
            )

        for i in predictoors_table_selected_rows:
            predictoors_addrs.append(predictoors_data[i]["user"])

        payouts = get_payouts_from_db(
            [item["contract"] for item in feeds_display_data],
            predictoors_addrs,
            app.lake_dir,
        )

        # get figures
        accuracy_fig, profit_fig, stakes_fig = get_figures(
            payouts, feeds_display_data, predictoors_addrs
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
