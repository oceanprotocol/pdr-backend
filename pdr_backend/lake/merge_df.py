from typing import List, Union

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.lake.plutil import set_col_values


@enforce_types
def merge_rawohlcv_dfs(rawohlcv_dfs: dict) -> pl.DataFrame:
    """
    @arguments
      rawohlcv_dfs -- see class docstring

    @return
      mergedohlcv_df -- see class docstring
    """
    raw_dfs = rawohlcv_dfs

    print("  Merge rawohlcv dataframes.")
    merged_df = None
    for exch_str in raw_dfs.keys():
        for pair_str, raw_df in raw_dfs[exch_str].items():
            assert "/" in str(pair_str), f"pair_str={pair_str} needs '/'"
            assert "timestamp" in raw_df.columns

            for raw_col in raw_df.columns:
                if raw_col == "timestamp":
                    continue
                signal_str = raw_col  # eg "close"
                merged_col = f"{exch_str}:{pair_str}:{signal_str}"
                merged_df = _add_df_col(merged_df, merged_col, raw_df, raw_col)

    merged_df = merged_df.select(_ordered_cols(merged_df.columns))  # type: ignore
    _verify_df_cols(merged_df)
    return merged_df


@enforce_types
def _add_df_col(
    merged_df: Union[pl.DataFrame, None],
    merged_col: str,  # eg "binance:BTC/USDT:close"
    raw_df: pl.DataFrame,
    raw_col: str,  # eg "close"
) -> pl.DataFrame:
    """
    Does polars equivalent of: merged_df[merged_col] = raw_df[raw_col].
    Tuned for this factory, by keeping "timestamp"
    """
    newraw_df = raw_df.with_columns(
        pl.col(raw_col).alias(merged_col),
    )
    newraw_df = newraw_df.select(["timestamp", merged_col])

    if merged_df is None:
        merged_df = newraw_df
    else:
        merged_df = merged_df.join(newraw_df, on="timestamp", how="outer")
        merged_df = merge_cols(merged_df, "timestamp", "timestamp_right")

    merged_df = merged_df.select(_ordered_cols(merged_df.columns))  # type: ignore
    _verify_df_cols(merged_df)
    return merged_df


@enforce_types
def merge_cols(df: pl.DataFrame, col1: str, col2: str) -> pl.DataFrame:
    """Keep the non-null versions of col1 & col2, in col1. Drop col2."""
    assert col1 in df
    if col2 not in df:
        return df
    n_rows = df.shape[0]
    new_vals = [df[col1][i] or df[col2][i] for i in range(n_rows)]
    df = set_col_values(df, col1, new_vals)
    df = df.drop(col2)
    return df


@enforce_types
def _ordered_cols(merged_cols: List[str]) -> List[str]:
    """Returns in order ["timestamp", item1, item2, item3, ...]"""
    assert "timestamp" in merged_cols
    assert len(set(merged_cols)) == len(merged_cols)

    ordered_cols = []
    ordered_cols += ["timestamp"]
    ordered_cols += [col for col in merged_cols if col != "timestamp"]
    return ordered_cols


@enforce_types
def _verify_df_cols(df: pl.DataFrame):
    assert "timestamp" in df.columns
    assert "datetime" not in df.columns
    for col in df.columns:
        assert "_right" not in col
        assert "_left" not in col
    assert df.columns == _ordered_cols(df.columns)
