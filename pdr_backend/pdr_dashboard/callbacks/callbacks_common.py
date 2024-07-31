from dash import Input, Output
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_navbar,
    NAV_ITEMS,
)
from pdr_backend.pdr_dashboard.pages import home, feeds


def get_callbacks_common(app):
    @app.callback(
        Output("page-content", "children"),
        Output("navbar-container", "children"),
        [Input("url", "pathname")],
    )
    def display_page(pathname):
        for item in NAV_ITEMS:
            item["active"] = item["location"].lower() == pathname
        if pathname == "/":
            return home.layout(app), get_navbar(NAV_ITEMS)
        if pathname == "/feeds":
            return feeds.layout(app), get_navbar(NAV_ITEMS)
        return "404 - Page not found", get_navbar(NAV_ITEMS)
