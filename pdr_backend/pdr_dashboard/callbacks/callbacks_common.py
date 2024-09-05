from dash import Input, Output
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_navbar,
    NAV_ITEMS,
)
from pdr_backend.pdr_dashboard.pages.home import HomePage
from pdr_backend.pdr_dashboard.pages.feeds import FeedsPage
from pdr_backend.pdr_dashboard.pages.predictoors import PredictoorsPage
from pdr_backend.pdr_dashboard.util.data import (
    get_date_period_text_header,
    get_start_date_from_period,
)


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

    @app.callback(
        Output("start-date", "data"),
        [Input("general-lake-date-period-radio-items", "value")],
    )
    def set_period_start_date(selected_period_start):
        start_date = (
            get_start_date_from_period(int(selected_period_start))
            if int(selected_period_start) > 0
            else None
        )
        app.start_date = start_date
        return start_date

    @app.callback(
        Output("available-data-text", "children"),
        [Input("page-content", "children")],
    )
    def display_available_data(_):
        return get_date_period_text_header(
            app.data.min_timestamp, app.data.max_timestamp
        )

    def get_page(pathname):
        if pathname not in ["/", "/feeds", "/predictoors"]:
            return "404 - Page not found"

        if pathname == "/":
            page = HomePage(app)
        elif pathname == "/feeds":
            page = FeedsPage(app)
        else:
            page = PredictoorsPage(app)

        return page.layout()
