from typing import Optional, Type
from pdr_backend.technical_indicators.indicators.macd import MACD
from pdr_backend.technical_indicators.indicators.rsi import RSI
from pdr_backend.technical_indicators.technical_indicator import TechnicalIndicator

indicators = {
    "rsi": RSI,
    "macd": MACD,
}

def get_ta_indicator(indicator: str) -> Optional[Type[TechnicalIndicator]]:
    """
    Returns the technical indicator class based on the input indicator name.
    """
    return indicators.get(indicator)    