import pandas as pd
import ta
from pdr_backend.technical_indicators.indicators.rsi import RSI


def test_rsi(sample_df):
    rsi_indicator = RSI(
        df=sample_df,
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )

    # Calculate RSI
    rsi_result = rsi_indicator.calculate(window=14)

    # Expected RSI calculation using `ta` library
    expected_rsi = ta.momentum.RSIIndicator(close=sample_df["close"], window=14).rsi()

    pd.testing.assert_series_equal(rsi_result, expected_rsi, check_dtype=False)
