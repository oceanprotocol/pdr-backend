import webbrowser

import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.analytics.predictoor_dashboard.dash_components.callbacks import (
    get_callbacks,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_payouts,
    get_user_payouts_stats_from_db,
)
from pdr_backend.analytics.predictoor_dashboard.dash_components.view_elements import (
    get_layout,
)
from pdr_backend.ppss.ppss import PPSS

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.config["suppress_callback_exceptions"] = True
app.layout = get_layout()


@enforce_types
def predictoor_dash(ppss: PPSS, debug_mode: bool):
    port = 8050
    if not debug_mode:
        webbrowser.open(f"http://127.0.0.1:{port}/")

    try:
        setup_app(app, ppss)
    except Exception as e:
        print(
            f"""ERROR: Please make sure there is data in the lake.
            Full error: {e}"""
        )
        return

    get_callbacks(app)
    app.run(debug=debug_mode, port=port)


@enforce_types
def setup_app(app, ppss: PPSS):
    app.lake_dir = ppss.lake_ss.lake_dir
    app.feeds_data = get_feeds_data_from_db(ppss.lake_ss.lake_dir)
    app.predictoors_data = get_predictoors_data_from_payouts(
        get_user_payouts_stats_from_db(ppss.lake_ss.lake_dir)
    )
    app.favourite_addresses = ppss.predictoor_ss.my_addresses

    return app
