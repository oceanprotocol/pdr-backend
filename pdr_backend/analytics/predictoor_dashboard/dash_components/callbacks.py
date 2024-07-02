from dash import Input, Output
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_table,
)


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(Output("feeds-data", "data"), Input("data-folder", "data"))
    def get_feeds_data(files_dir):
        feeds_data = get_feeds_data_from_db(files_dir)
        return feeds_data

    @app.callback(Output("feeds_container", "children"), Input("feeds-data", "data"))
    def create_feeds_table(feeds_data):
        if not feeds_data:
            return dash.no_update
        columns = feeds_data[0].keys()
        table = get_table(columns, feeds_data)
        return table
