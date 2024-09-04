from pdr_backend.technical_indicators.get_indicator import get_ta_indicator
from pdr_backend.technical_indicators.indicators.macd import MACD
from pdr_backend.technical_indicators.indicators.rsi import RSI


def test_get_ta_indicator_valid():
    assert get_ta_indicator("rsi") == RSI
    assert get_ta_indicator("macd") == MACD


def test_get_ta_indicator_invalid():
    assert get_ta_indicator("invalid_indicator") is None


def test_get_ta_indicator_case_sensitivity():
    assert get_ta_indicator("RSI") is None
    assert get_ta_indicator("MACD") is None
