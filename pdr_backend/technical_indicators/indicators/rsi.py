import pandas as pd
import ta
from pdr_backend.technical_indicators.technical_indicator import TechnicalIndicator


class RSI(TechnicalIndicator):
    """
    Relative Strength Index (RSI) technical indicator.
    """

    def calculate(self, window: int = 14) -> pd.Series:
        """
        Calculates the RSI value based on the input data.

        @param:
            window - The window size for the RSI calculation (default=14).
        """
        rsi = ta.momentum.RSIIndicator(close=self._close(), window=window).rsi()
        return rsi
