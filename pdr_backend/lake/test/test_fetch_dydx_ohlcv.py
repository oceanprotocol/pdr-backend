import pytest
# from enforce_typing import enforce_types

from pdr_backend.lake.fetch_ohlcv import safe_fetch_ohlcv_dydx, fetch_dydx_data, transform_dydx_data_to_df, transform_dydx_data_to_tuples
from pdr_backend.util.time_types import UnixTimeMs

from pdr_backend.util.constants import (
    CAND_USDCOINS,
    CAND_TIMEFRAMES,
)

def test_fetch_dydx_data():

    start_date = UnixTimeMs.from_timestr("2024-02-21_00:00")
    end_date = UnixTimeMs.from_timestr("2024-02-21_00:15")
    symbol, resolution, st_ut, fin_ut, limit = "BTC-USD", "5MINS", start_date, end_date, 100

    # happy path
    result = safe_fetch_ohlcv_dydx(symbol, resolution, st_ut, fin_ut, limit)
    assert result is not None

#     # # Catches TypeErrors for incorrect dates
#     # with pytest.raises(TypeError):
#     #     fetch_dydx_data(symbol, resolution, "abc", fin_ut)
#     # with pytest.raises(TypeError):
#     #     fetch_dydx_data(symbol, resolution, st_ut, "abc")

#     # with pytest.raises(TypeError):
#     #     fetch_dydx_data("RANDOMTOKEN-USD", resolution, st_ut, fin_ut)
#     # with pytest.raises(TypeError):
#     #     fetch_dydx_data(symbol, "123mins", st_ut, fin_ut)

#     # Convert symbol
#     normalized_symbol = symbol.replace("-", "/")
#     base, quote = normalized_symbol.split("/")
#     if quote in CAND_USDCOINS:
#         symbol = base + "-USD"
#     else:
#         print("Please input a token paired with a stablecoin or USD for dydx.")

# # def validate_resolution(timeframe: str) -> None:
# #     """
# #     Validates the input timeframe string.

# #     :param timeframe: The timeframe string to validate.
# #     :raises AssertionError: If the timeframe is not one of the allowed values.
# #     """
# #     allowed_values = {"1MIN", "5MINS", "15MINS", "30MINS", "1HOUR", "4HOURS", "1DAY"}
# #     assert timeframe in allowed_values, f"Invalid resolution: {timeframe}. Allowed values are: {allowed_values}"

# # # Example Usage
# # try:
# #     validate_resolution("1MIN")    # Valid input
# #     validate_resolution("10MINS")  # Invalid input, will raise AssertionError
# # except AssertionError as e:
# #     print(e)

