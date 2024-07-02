from dash import Input, Output, State
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_payouts_from_db,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_table,
    get_graph,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.plots import get_figures


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        Output("feeds-data", "data"),
        Output("predictoors-data", "data"),
        Input("data-folder", "data"),
    )
    def get_input_data_from_db(files_dir):
        feeds_data = get_feeds_data_from_db(files_dir)
        predictoors_data = get_predictoors_data_from_db(files_dir)
        return feeds_data, predictoors_data

    @app.callback(
        Output("payouts-data", "data"),
        [
            Input("feeds_table", "selected_rows"),
            Input("predictoors_table", "selected_rows"),
        ],
        State("feeds-data", "data"),
        State("predictoors-data", "data"),
        State("data-folder", "data"),
    )
    def get_display_data_from_db(
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_data,
        predictoors_data,
        lake_dir,
    ):
        feeds_addrs = []
        predictoors_addrs = []
        if len(feeds_table_selected_rows) == 0:
            return dash.no_update

        for i in feeds_table_selected_rows:
            feeds_addrs.append(feeds_data[i]["contract"])

        for i in predictoors_table_selected_rows:
            predictoors_addrs.append(predictoors_data[i]["user"])

        payouts = get_payouts_from_db(feeds_addrs, predictoors_addrs, lake_dir)

        return payouts

    @app.callback(Output("feeds_container", "children"), Input("feeds-data", "data"))
    def create_feeds_table(feeds_data):
        if not feeds_data:
            return dash.no_update
        for feed in feeds_data:
            del feed["contract"]
        columns = feeds_data[0].keys()
        table = get_table(
            table_id="feeds_table", table_name="Feeds", columns=columns, data=feeds_data
        )
        return table

    @app.callback(
        Output("predictoors_container", "children"), Input("predictoors-data", "data")
    )
    def create_predictoors_table(predictoors_data):
        if not predictoors_data:
            return dash.no_update
        columns = predictoors_data[0].keys()
        table = get_table(
            table_id="predictoors_table",
            table_name="Predictoors",
            columns=columns,
            data=predictoors_data,
        )
        return table

    @app.callback(
        Output("accuracy_chart", "children"),
        Output("profit_chart", "children"),
        Input("payouts-data", "data"),
        Input("feeds_table", "selected_rows"),
        Input("predictoors_table", "selected_rows"),
        State("feeds-data", "data"),
        State("predictoors-data", "data"),
    )
    def create_charts(
        payouts_data,
        feeds_table_selected_rows,
        predictoors_table_selected_rows,
        feeds_data,
        predictoors_data,
    ):
        feeds_addrs = []
        predictoors_addrs = []
        for i in feeds_table_selected_rows:
            feeds_addrs.append(feeds_data[i]["contract"])

        for i in predictoors_table_selected_rows:
            predictoors_addrs.append(predictoors_data[i]["user"])

        accuracy_fig, profit_fig = get_figures(
            payouts_data, feeds_addrs, predictoors_addrs
        )
        return get_graph(accuracy_fig), get_graph(profit_fig)
