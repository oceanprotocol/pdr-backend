import webbrowser

import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.pdr_dashboard.callbacks.callbacks_common import get_callbacks_common
from pdr_backend.pdr_dashboard.callbacks.callbacks_feeds import get_callbacks_feeds
from pdr_backend.pdr_dashboard.callbacks.callbacks_home import get_callbacks_home
from pdr_backend.pdr_dashboard.callbacks.callbacks_predictoors import (
    get_callbacks_predictoors,
)
from pdr_backend.pdr_dashboard.dash_components.view_elements import get_layout
from pdr_backend.pdr_dashboard.util.db import AppDataManager
from pdr_backend.ppss.ppss import PPSS


@enforce_types
def predictoor_dash(ppss: PPSS, debug_mode: bool):
    port = 8050
    if not debug_mode:
        webbrowser.open(f"http://127.0.0.1:{port}/")

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    setup_app(app, ppss)
    app.run(debug=debug_mode, port=port)


@enforce_types
def setup_app(app, ppss: PPSS):
    app.web3_pp = ppss.web3_pp

    app.data = AppDataManager(ppss)
    app.layout = get_layout()

    get_callbacks_home(app)
    get_callbacks_feeds(app)
    get_callbacks_predictoors(app)
    get_callbacks_common(app)
    return app
