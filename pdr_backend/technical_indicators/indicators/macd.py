import pandas as pd
import ta
from pdr_backend.technical_indicators.technical_indicator import TechnicalIndicator


class MACD(TechnicalIndicator):
    """
    Moving Average Convergence Divergence (MACD) technical indicator.
    """

    def calculate(self, window_fast: int = 12, window_slow: int = 26) -> pd.Series:
        """
        Calculates the MACD value based on the input data.

        @param:
            window_fast - The window size for the fast EMA calculation (default=12).
            window_slow - The window size for the slow EMA calculation (default=26).
        """
        macd = ta.trend.MACD(
            close=self._close(), window_fast=window_fast, window_slow=window_slow
        )
        return macd.macd()
