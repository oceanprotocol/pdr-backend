import webbrowser

from datetime import datetime
import dash_bootstrap_components as dbc
from dash import Dash
from enforce_typing import enforce_types
from pdr_backend.exchange.fetch_ohlcv import fetch_ohlcv
from pdr_backend.util.time_types import UnixTimeMs

from pdr_backend.pdr_dashboard.dash_components.callbacks import (
    get_callbacks,
)
from pdr_backend.pdr_dashboard.dash_components.util import (
    get_feeds_data_from_db,
    get_predictoors_data_from_payouts,
    get_user_payouts_stats_from_db,
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

    get_callbacks(app)
    app.run(debug=debug_mode, port=port)


@enforce_types
def setup_app(app, ppss: PPSS):
    app.web3_pp = ppss.web3_pp
    app.lake_dir = ppss.lake_ss.lake_dir
    app.feeds_data = get_feeds_data_from_db(ppss.lake_ss.lake_dir)
    app.predictoors_data = get_predictoors_data_from_payouts(
        get_user_payouts_stats_from_db(ppss.lake_ss.lake_dir)
    )
    app.favourite_addresses = ppss.predictoor_ss.my_addresses
    app.layout = get_layout(app)

    # fetch token prices
    current_date_ms = UnixTimeMs(int(datetime.now().timestamp()) * 1000 - 300000)
    rose_usdt = fetch_ohlcv("binance", "ROSE/USDT", "5m", current_date_ms, 1)
    fet_usdt = fetch_ohlcv("binance", "FET/USDT", "5m", current_date_ms, 1)
    if rose_usdt and fet_usdt:
        app.prices = {"ROSE": rose_usdt[0][1], "OCEAN": fet_usdt[0][1] * 0.433226}
    else:
        rose_usdt = fetch_ohlcv("binanceus", "ROSE/USDT", "5m", current_date_ms, 1)
        fet_usdt = fetch_ohlcv("binanceus", "FET/USDT", "5m", current_date_ms, 1)
        if rose_usdt and fet_usdt:
            app.prices = {"ROSE": rose_usdt[0][1], "OCEAN": fet_usdt[0][1] * 0.433226}
        else:
            app.prices = None

    return app
