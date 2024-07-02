from dash import Input, Output
import dash
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_db,
    get_predictoors_stake_data_from_db,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_table,
    get_predictoors_stake_graph,
)


# pylint: disable=too-many-statements
def get_callbacks(app):
    @app.callback(
        Output("feeds-data", "data"),
        Output("predictoors-data", "data"),
        Output("predictoors-stake-data", "data"),
        Input("data-folder", "data"),
    )
    def get_data_from_db(files_dir):
        feeds_data = get_feeds_data_from_db(files_dir)
        predictoors_data = get_predictoors_data_from_db(files_dir)
        predictoors_stake_Data = get_predictoors_stake_data_from_db(files_dir)
        return feeds_data, predictoors_data, predictoors_stake_Data

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
        Output("predictoors_stake_container", "children"),
        Input("feeds_table", "selected_rows"),
        Input("feeds_table", "data"),
        Input("predictoors-stake-data", "data"),
    )
    def create_predictoors_stake_graph(
        selected_feeds, feeds_table_data, predictoors_stake_data):
        if not predictoors_stake_data:
            return dash.no_update

        selected_sources = [row["source"] for row in feeds_table_data]
        selected_timeframes = [row["timeframe"] for row in feeds_table_data]
        selected_pairs = [row["pair"] for row in feeds_table_data]

        if selected_feeds:
            predictoors_stake_data = [
                row for row in predictoors_stake_data 
                if row["source"] in selected_sources and
                row["timeframe"] in selected_timeframes and
                row["pair"] in selected_pairs
            ]

        fig = get_predictoors_stake_graph(predictoors_stake_data)
        return fig
