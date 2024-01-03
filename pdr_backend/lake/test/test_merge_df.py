import polars as pl
import pytest
from enforce_typing import enforce_types

from pdr_backend.lake.merge_df import (
    _add_df_col,
    _ordered_cols,
    merge_cols,
    merge_rawohlcv_dfs,
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
    ]
    assert mergedohlcv_df.shape == (12, 6)
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
    ]
    assert merged_df["timestamp"][1] == 1
    assert merged_df["binance:BTC/USDT:close"][3] == 11.3
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3
    assert merged_df["kraken:ETH/USDT:open"][4] == 40.4


@enforce_types
def test_add_df_col_unequal_dfs():
    # basic sanity test that floats are floats
    assert isinstance(RAW_DF1["close"][1], float)

    # add a first RAW_DF
    merged_df = _add_df_col(None, "binance:BTC/USDT:close", RAW_DF1, "close")
    assert merged_df.columns == ["timestamp", "binance:BTC/USDT:close"]
    assert merged_df.shape == (4, 2)
    assert merged_df["timestamp"][1] == 1
    assert merged_df["binance:BTC/USDT:close"][3] == 11.4

    # add a second RAW_DF
    merged_df = _add_df_col(merged_df, "binance:ETH/USDT:open", RAW_DF2, "open")
    assert merged_df.columns == [
        "timestamp",
        "binance:BTC/USDT:close",
        "binance:ETH/USDT:open",
    ]
    assert merged_df.shape == (5, 3)
    assert merged_df["timestamp"][1] == 1
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
    ]
    assert merged_df.shape == (5, 2)
    assert merged_df["timestamp"][1] == 1
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3

    # add a second RAW_DF
    merged_df = _add_df_col(merged_df, "kraken:ETH/USDT:open", RAW_DF4, "open")
    assert merged_df.columns == [
        "timestamp",
        "kraken:BTC/USDT:close",
        "kraken:ETH/USDT:open",
    ]
    assert merged_df.shape == (5, 3)
    assert merged_df["timestamp"][1] == 1
    assert merged_df["kraken:BTC/USDT:close"][3] == 31.3
    assert merged_df["kraken:ETH/USDT:open"][4] == 40.4


@enforce_types
def test_merge_cols():
    df = pl.DataFrame(
        {
            "a": [1, 2, 3, 4],
            "b": [5, 6, 7, None],
            "c": [9, 9, 9, 9],
        }
    )  # None will become pl.Null

    df = df.select(["a", "b", "c"])
    assert df.columns == ["a", "b", "c"]

    # merge b into a
    df2 = merge_cols(df, "a", "b")
    assert df2.columns == ["a", "c"]
    assert df2["a"].to_list() == [1, 2, 3, 4]

    # merge a into b
    df3 = merge_cols(df, "b", "a")
    assert df3.columns == ["b", "c"]
    assert df3["b"].to_list() == [5, 6, 7, 4]  # the 4 comes from "a"


@enforce_types
def test_ordered_cols():
    assert _ordered_cols(["timestamp"]) == ["timestamp"]
    assert _ordered_cols(["a", "c", "b", "timestamp"]) == [
        "timestamp",
        "a",
        "c",
        "b",
    ]

    for bad_cols in [
        ["a", "c", "b"],  # missing timestamp
        ["a", "c", "b", "b", "timestamp"],  # duplicates
        ["a", "c", "b", "timestamp", "timestamp"],  # duplicates
    ]:
        with pytest.raises(AssertionError):
            _ordered_cols(bad_cols)
