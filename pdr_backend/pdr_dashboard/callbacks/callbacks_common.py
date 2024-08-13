from dash import Input, Output
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_navbar,
    NAV_ITEMS,
)
from pdr_backend.pdr_dashboard.pages.home import HomePage
from pdr_backend.pdr_dashboard.pages.feeds import FeedsPage


def get_callbacks_common(app):
    @app.callback(
        Output("page-content", "children"),
        Output("navbar-container", "children"),
        [Input("url", "pathname")],
    )
    def display_page(pathname):
        for item in NAV_ITEMS:
            item["active"] = item["location"].lower() == pathname

        result = get_page(pathname), get_navbar(NAV_ITEMS)
        return result

    def get_page(pathname):
        if pathname not in ["/", "/feeds"]:
            return "404 - Page not found"

        page = HomePage(app) if pathname == "/" else FeedsPage(app)

        return page.layout()
