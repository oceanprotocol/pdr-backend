from dash import Input, Output, dash

from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    NAV_ITEMS,
    get_navbar,
)
from pdr_backend.pdr_dashboard.pages.feeds import FeedsPage
from pdr_backend.pdr_dashboard.pages.home import HomePage
from pdr_backend.pdr_dashboard.pages.predictoors import PredictoorsPage
from pdr_backend.pdr_dashboard.util.helpers import (
    get_date_period_text_header,
    with_loading,
    check_data_loaded,
)


def get_callbacks_common(app):
    @app.callback(
        Output("is-initial-data-loaded", "data"),
        Input("is-initial-data-loaded", "data"),
    )
    def initial_data_load(is_data_loaded):
        if not is_data_loaded or not is_data_loaded["loaded"]:
            print("Initial data load")
            app.data.initial_process()  # Call the initial process
            return {"loaded": True}

        return dash.no_update

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
        [
            Input("general-lake-date-period-radio-items", "value"),
            Input("is-initial-data-loaded", "data"),
        ],
    )
    @check_data_loaded(output_count=1)
    def set_period_start_date(
        selected_period_start,
        _,
    ):
        app.data.set_start_date_from_period(int(selected_period_start))
        return app.data.start_date

    @app.callback(
        Output("available-data-text", "children"),
        [
            Input("page-content", "children"),
            Input("is-initial-data-loaded", "data"),
        ],
        prevent_initial_call=True,
    )
    @with_loading("loading-available-period")
    @check_data_loaded(output_count=1, alternative_output="")
    def display_available_data(
        _,
        is_initial_data_loaded,
    ):
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
