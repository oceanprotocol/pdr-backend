import dash_bootstrap_components as dbc
from dash import Input, Output, State


def get_callbacks_feeds(app):
    @app.callback(
        Output("modal", "is_open"),
        Output("modal", "children"),
        [
            Input("feeds_table", "active_cell"),
        ],
        State("feeds_table", "data"),
    )
    def update_graphs(active_cell, feeds_table_data):
        open_modal = True if active_cell else False

        if not open_modal:
            return open_modal, []

        selected_row = feeds_table_data[active_cell["row"]]

        children = [
            # TODO: adjust content for header and body
            dbc.ModalHeader("Header"),
            dbc.ModalBody(str(selected_row)),
        ]

        return open_modal, children
