# import pytest
# from enforce_typing import enforce_types

# from pdr_backend.cli.arg_feed import ArgFeed
# from pdr_backend.lake.fetch_ohlcv import fetch_dydx_data, transform_dydx_data
# # from pdr_backend.util.time_types import ***
from pdr_backend.util.constants import (
    CAND_USDCOINS,
    CAND_TIMEFRAMES,
)

# # TODO ALL THIS NEEDS TO BE REDONE TO WORK WITH THE LATEST time_types util file

# # def test_fetch_dydx_data():

#     # start_date = timestr_to_ut("2024-02-21_00:00")
#     # end_date = timestr_to_ut("2024-02-21_00:15")
#     # symbol, resolution, st_ut, fin_ut = "BTC-USD", "5MINS", start_date, end_date

#     # # happy path
#     # df = fetch_dydx_data(symbol, resolution, st_ut, fin_ut)
#     # assert not df.is_empty()

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

