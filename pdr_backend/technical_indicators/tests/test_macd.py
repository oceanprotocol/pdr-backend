import pandas as pd
import ta
from pdr_backend.technical_indicators.indicators.macd import MACD


def test_macd(sample_df):
    macd_indicator = MACD(
        df=sample_df,
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )

    macd_result = macd_indicator.calculate(window_fast=12, window_slow=26)

    expected_macd = ta.trend.MACD(
        close=sample_df["close"], window_fast=12, window_slow=26
    ).macd()

    pd.testing.assert_series_equal(macd_result, expected_macd, check_dtype=False)
