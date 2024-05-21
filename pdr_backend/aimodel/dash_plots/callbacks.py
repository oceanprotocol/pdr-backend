from dash import Input, Output, State
import pandas as pd
from scipy import stats
from pdr_backend.aimodel.dash_plots.util import get_figures_by_state
from pdr_backend.aimodel.dash_plots.view_elements import (
    get_header_elements,
)
from pdr_backend.aimodel.autocorrelation import AutocorrelationPlotdataFactory


def get_callbacks(app):
    @app.callback(
        Output('data-store', 'data'),
        Input('arima-graphs', 'id'),
        State("selected_vars", "value")
    )
    # pylint: disable=unused-argument
    def load_data():
        nlags = 5
        do_boxcox = True
        differencing_order = 1

        df = pd.read_csv('../../parquet_data/binance_BTC-USDT_5m')  # all data start_time = UnixTimeMs(df["timestamp"][0])
        BTC_COL = "binance:BTC/USDT:close"
        y = df[BTC_COL].array
        if do_boxcox:
            y, _ = stats.boxcox(y)
        for _ in range(differencing_order):
            y = y[1:] - y[:-1]

        data = AutocorrelationPlotdataFactory.build(y, nlags)
        elements = get_header_elements()

        elements.append(data)

        return elements
    
    @app.callback(
        Output('data-store', 'data'),
        Input('arima-graphs', 'id'),
        State("selected_vars", "value")
    )
    # pylint: disable=unused-argument
    def create_charts(n, selected_vars, selected_vars_old):
