from typing import List, Union

from enforce_typing import enforce_types

import polars as pl


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
            assert "/" in pair_str, f"pair_str={pair_str} needs '/'"
            assert "datetime" in raw_df.columns
            assert "timestamp" in raw_df.columns

            for raw_col in raw_df.columns:
                if raw_col in ["timestamp", "datetime"]:
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
    Tuned for this factory, by keeping "timestamp" & "datetime"
    """
    newraw_df = raw_df.with_columns(
        pl.col(raw_col).alias(merged_col),
    )
    newraw_df = newraw_df.select(["timestamp", merged_col, "datetime"])

    if merged_df is None:
        merged_df = newraw_df
    else:
        merged_df = merged_df.join(newraw_df, on=["timestamp", "datetime"], how="outer")
        merged_df = _merge_cols(merged_df, "timestamp", "timestamp_right")
        merged_df = _merge_cols(merged_df, "datetime", "datetime_right")

    merged_df = merged_df.select(_ordered_cols(merged_df.columns))  # type: ignore
    _verify_df_cols(merged_df)
    return merged_df


@enforce_types
def _merge_cols(df: pl.DataFrame, col1: str, col2: str) -> pl.DataFrame:
    """Keep the non-null versions of col1 & col2, in col1. Drop col2."""
    assert col1 in df
    if col2 not in df:
        return df
    for i in range(df.shape[1]):
        df[col1][i] = df[col1][i] or df[col2][i]
    df = df.drop(col2)
    return df


@enforce_types
def _ordered_cols(merged_cols: List[str]) -> List[str]:
    """Returns in order ["timestamp", item1, item2, item3, ..., "datetime"]"""
    assert "timestamp" in merged_cols
    assert "datetime" in merged_cols
    assert len(set(merged_cols)) == len(merged_cols)

    ordered_cols = []
    ordered_cols += ["timestamp"]
    ordered_cols += [col for col in merged_cols if col not in ["timestamp", "datetime"]]
    ordered_cols += ["datetime"]
    return ordered_cols


@enforce_types
def _verify_df_cols(df: pl.DataFrame):
    assert "datetime" in df.columns
    assert "timestamp" in df.columns
    for col in df.columns:
        assert "_right" not in col
        assert "_left" not in col
    assert df.columns == _ordered_cols(df.columns)
