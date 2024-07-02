from dash import Input, Output
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_table,
)


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        Output("feeds-data", "data"),
        Output("predictoors-data", "data"),
        Input("data-folder", "data"),
    )
    def get_data_from_db(files_dir):
        feeds_data = get_feeds_data_from_db(files_dir)
        predictoors_data = get_predictoors_data_from_db(files_dir)
        return feeds_data, predictoors_data

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
