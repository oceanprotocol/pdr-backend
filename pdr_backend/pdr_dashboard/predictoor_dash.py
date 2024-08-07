import webbrowser

import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.pdr_dashboard.callbacks.callbacks_feeds import (
    get_callbacks_feeds,
)
from pdr_backend.pdr_dashboard.callbacks.callbacks_home import (
    get_callbacks_home,
)
from pdr_backend.pdr_dashboard.callbacks.callbacks_common import (
    get_callbacks_common,
)
from pdr_backend.pdr_dashboard.util.db import DBGetter
from pdr_backend.pdr_dashboard.util.data import get_predictoors_data_from_payouts
from pdr_backend.pdr_dashboard.util.prices import (
    fetch_token_prices,
)
from pdr_backend.pdr_dashboard.dash_components.view_elements import (
    get_layout,
)
from pdr_backend.ppss.ppss import PPSS


@enforce_types
def predictoor_dash(ppss: PPSS, debug_mode: bool):
    port = 8050
    if not debug_mode:
        webbrowser.open(f"http://127.0.0.1:{port}/")

    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app.config["suppress_callback_exceptions"] = True

    try:
        setup_app(app, ppss)
    except Exception as e:
        print(
            f"""ERROR: Please make sure there is data in the lake.
            Full error: {e}"""
        )
        return

    app.run(debug=debug_mode, port=port)


@enforce_types
def setup_app(app, ppss: PPSS):
    app.web3_pp = ppss.web3_pp
    app.db_getter = DBGetter(ppss.lake_ss.lake_dir)
    app.network_name = ppss.web3_pp.network

    app.feeds_data = app.db_getter.feeds_data()
    app.predictoors_data = get_predictoors_data_from_payouts(
        app.db_getter.payouts_stats()
    )

    valid_addresses = [p["user"].lower() for p in app.predictoors_data]
    app.favourite_addresses = [
        addr for addr in ppss.predictoor_ss.my_addresses if addr in valid_addresses
    ]

    app.layout = get_layout()

    # fetch token prices
    app.prices = fetch_token_prices()

    get_callbacks_home(app)
    get_callbacks_feeds(app)
    get_callbacks_common(app)
    return app
