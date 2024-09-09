from abc import ABC, abstractmethod
from enforce_typing import enforce_types
import pandas as pd


@enforce_types
class TechnicalIndicator(ABC):
    """
    Abstract base class for technical indicators.

    Attributes:
        df - pd.DataFrame
            The input dataframe containing the time series data.
        open - str
            The name of the column containing opening price data.
        high - str
            The name of the column containing high price data.
        low - str
            The name of the column containing low price data.
        close - str
            The name of the column containing closing price data.
        volume - str
            The name of the column containing volume data.

    Methods:
        calculate(*args, **kwargs) -> pd.Series
            Calculates the indicator value based on the input data.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        open_col: str,
        high_col: str,
        low_col: str,
        close_col: str,
        volume_col: str,
    ):
        """
        Initializes a TechnicalIndicator object.
            @param:
                open - name of column containing opening price data,
                high - name of column containing high price data,
                low - name of column containing low price data,
                close - name of column containing closing price data,
                volume - name of column containing volume data,
        """
        self.df = df
        self.open_col = open_col
        self.high_col = high_col
        self.low_col = low_col
        self.close_col = close_col
        self.volume_col = volume_col

    def _open(self):
        return self.df[self.open_col]

    def _high(self):
        return self.df[self.high_col]

    def _low(self):
        return self.df[self.low_col]

    def _close(self):
        return self.df[self.close_col]

    def _volume(self):
        return self.df[self.volume_col]

    @abstractmethod
    def calculate(self, *args, **kwargs) -> pd.Series:
        """
        Calculates the indicator value based on the input data.

        @return
            pd.Series - the indicator.
        """


class MockTechnicalIndicator(TechnicalIndicator):
    def calculate(self, *args, **kwargs) -> pd.Series:
        # Example implementation for testing purposes
        return self._close() * 0.5
