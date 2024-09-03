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

    def __init__(self, df: pd.DataFrame, open: str, high: str, low: str, close: str, volume: str):
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
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def _open(self):
        return self.df[self.open]

    def _high(self):
        return self.df[self.high]
    
    def _low(self):
        return self.df[self.low]
    
    def _close(self):
        return self.df[self.close]
    
    def _volume(self):
        return self.df[self.volume]
    
    @abstractmethod
    def calculate(self, *args, **kwargs) -> pd.Series:
        """
        Calculates the indicator value based on the input data.

        @return
            pd.Series - the indicator.
        """
        pass
