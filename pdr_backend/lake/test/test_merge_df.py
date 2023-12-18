from enforce_typing import enforce_types
import polars as pl
import pytest

from pdr_backend.lake.merge_df import (
    merge_rawohlcv_dfs,
    _add_df_col,
    _ordered_cols,
)
from pdr_backend.lake.test.resources import (
    ETHUSDT_RAWOHLCV_DFS,
    RAW_DF1,
    RAW_DF2,
    RAW_DF3,
    RAW_DF4,
)


@enforce_types
def test_mergedohlcv_df_shape():
    mergedohlcv_df = merge_rawohlcv_dfs(ETHUSDT_RAWOHLCV_DFS)
    assert isinstance(mergedohlcv_df, pl.DataFrame)
    assert mergedohlcv_df.columns == [
        "timestamp",
        "binanceus:ETH/USDT:open",
        "binanceus:ETH/USDT:high",
        "binanceus:ETH/USDT:low",
        "binanceus:ETH/USDT:close",
        "binanceus:ETH/USDT:volume",
        "datetime",
    ]
    assert mergedohlcv_df.shape == (12, 7)
    assert len(mergedohlcv_df["timestamp"]) == 12
    assert (  # pylint: disable=unsubscriptable-object
        mergedohlcv_df["timestamp"][0] == 1686805500000
    )


@enforce_types
def test_merge_rawohlcv_dfs():
    raw_dfs = {
        "binance": {"BTC/USDT": RAW_DF1, "ETH/USDT": RAW_DF2},
        "kraken": {"BTC/USDT": RAW_DF3, "ETH/USDT": RAW_DF4},
    }

    merged_df = merge_rawohlcv_dfs(raw_dfs)

    assert merged_df.columns == [
        "timestamp",
        "binance:BTC/USDT:open",
        "binance:BTC/USDT:close",
        "binance:ETH/USDT:open",
        "binance:ETH/USDT:close",
        "kraken:BTC/USDT:open",
        "kraken:BTC/USDT:close",
        "kraken:ETH/USDT:open",
        "kraken:ETH/USDT:close",
        "datetime",
    ]
    assert merged_df["datetime"][1] == "d1"
    assert merged_df["binance:BTC/USDT:close"][3] == 11.3
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3
    assert merged_df["kraken:ETH/USDT:open"][4] == 40.4


@enforce_types
def test_add_df_col_unequal_dfs():
    # basic sanity test that floats are floats
    assert isinstance(RAW_DF1["close"][1], float)

    # add a first RAW_DF
    merged_df = _add_df_col(None, "binance:BTC/USDT:close", RAW_DF1, "close")
    assert merged_df.columns == ["timestamp", "binance:BTC/USDT:close", "datetime"]
    assert merged_df.shape == (4, 3)
    assert merged_df["datetime"][1] == "d1"
    assert merged_df["binance:BTC/USDT:close"][3] == 11.4

    # add a second RAW_DF
    merged_df = _add_df_col(merged_df, "binance:ETH/USDT:open", RAW_DF2, "open")
    assert merged_df.columns == [
        "timestamp",
        "binance:BTC/USDT:close",
        "binance:ETH/USDT:open",
        "datetime",
    ]
    assert merged_df.shape == (5, 4)
    assert merged_df["datetime"][1] == "d1"
    assert merged_df["binance:BTC/USDT:close"][3] == 11.3
    assert merged_df["binance:ETH/USDT:open"][3] == 20.3


@enforce_types
def test_add_df_col_equal_dfs():
    # basic sanity test that floats are floats
    assert isinstance(RAW_DF3["close"][1], float)

    # add a first RAW_DF
    merged_df = _add_df_col(None, "kraken:BTC/USDT:close", RAW_DF3, "close")
    assert merged_df.columns == [
        "timestamp",
        "kraken:BTC/USDT:close",
        "datetime",
    ]
    assert merged_df.shape == (5, 3)
    assert merged_df["datetime"][1] == "d1"
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3

    # add a second RAW_DF
    merged_df = _add_df_col(merged_df, "kraken:ETH/USDT:open", RAW_DF4, "open")
    assert merged_df.columns == [
        "timestamp",
        "kraken:BTC/USDT:close",
        "kraken:ETH/USDT:open",
        "datetime",
    ]
    assert merged_df.shape == (5, 4)
    assert merged_df["datetime"][1] == "d1"
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3
    assert merged_df["kraken:ETH/USDT:open"][4] == 40.4


@enforce_types
def test_ordered_cols():
    assert _ordered_cols(["datetime", "timestamp"]) == ["timestamp", "datetime"]
    assert _ordered_cols(["a", "c", "b", "datetime", "timestamp"]) == [
        "timestamp",
        "a",
        "c",
        "b",
        "datetime",
    ]

    for bad_cols in [
        ["a", "c", "b", "datetime"],  # missing timestamp
        ["a", "c", "b", "timestamp"],  # missing datetime
        ["a", "c", "b", "b", "datetime", "timestamp"],  # duplicates
        ["a", "c", "b", "timestamp", "datetime", "timestamp"],  # duplicates
    ]:
        with pytest.raises(AssertionError):
            _ordered_cols(bad_cols)
