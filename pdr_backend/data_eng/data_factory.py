import os
import sys
from typing import Dict, List, Tuple, Union

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    OHLCV_MULT_MIN,
    OHLCV_MULT_MAX,
    TOHLCV_DTYPES_PL,
)
from pdr_backend.data_eng.plutil import (
    initialize_df,
    transform_df,
    concat_next_df,
    load_parquet,
    save_parquet,
    has_data,
    oldest_ut,
    newest_ut,
)
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.util.mathutil import has_nan, fill_nans
from pdr_backend.util.timeutil import pretty_timestr, current_ut


@enforce_types
class DataFactory:
    """
    Roles:
    - From each CEX API, fill >=1 parquet_dfs -> parquet files data lake
    - From parquet_dfs, fill 1 hist_df -- historical data across all CEXes
    - From hist_df, create (X, y, x_df) -- for model building

    Where:
      parquet_dfs -- dict of [exch_str][pair_str] : df
        And df has columns of: "open", "high", .., "volume", "datetime"
        (and index = timestamp)

      hist_df -- polars DataFrame with cols like:
        "timestamp",
        "binanceus:ETH-USDT:open",
        "binanceus:ETH-USDT:high",
        "binanceus:ETH-USDT:low",
        "binanceus:ETH-USDT:close",
        "binanceus:ETH-USDT:volume",
        ...
        "datetime",
        (and no index)

    And:
      X -- 2d array of [sample_i, var_i] : value -- inputs for model
      y -- 1d array of [sample_i] -- target outputs for model

      x_df -- *pandas* DataFrame with cols like:
        "binanceus:ETH-USDT:open:t-3",
        "binanceus:ETH-USDT:open:t-2",
        "binanceus:ETH-USDT:open:t-1",
        "binanceus:ETH-USDT:high:t-3",
        "binanceus:ETH-USDT:high:t-2",
        "binanceus:ETH-USDT:high:t-1",
        ...
        "datetime",
        (and index = 0, 1, .. -- nothing special)

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
       - "datetime" values ares python datetime.datetime, UTC
    """

    def __init__(self, pp: DataPP, ss: DataSS):
        self.pp = pp
        self.ss = ss

    def get_hist_df(self) -> pl.DataFrame:
        """
        @description
          Get historical dataframe, across many exchanges & pairs.

        @return
          hist_df -- *polars* Dataframe. See class docstring
        """
        print("Get historical data, across many exchanges & pairs: begin.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut
        fin_ut = self.ss.fin_timestamp

        print(f"  Data start: {pretty_timestr(self.ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(fin_ut)}")

        self._update_parquet(fin_ut)
        parquet_dfs = self._load_parquet(fin_ut)
        hist_df = self._merge_parquet_dfs(parquet_dfs)

        print("Get historical data, across many exchanges & pairs: done.")

        # postconditions
        assert isinstance(hist_df, pl.DataFrame)
        return hist_df

    def _update_parquet(self, fin_ut: int):
        print("  Update parquet.")
        for exch_str, pair_str in self.ss.exchange_pair_tups:
            self._update_hist_parquet_at_exch_and_pair(exch_str, pair_str, fin_ut)

    def _update_hist_parquet_at_exch_and_pair(
        self, exch_str: str, pair_str: str, fin_ut: int
    ):
        assert "-" in pair_str, f"pair_str '{pair_str}' needs '-'"
        print(f"    Update parquet at exchange={exch_str}, pair={pair_str}.")

        filename = self._hist_parquet_filename(exch_str, pair_str)
        print(f"      filename={filename}")

        st_ut = self._calc_start_ut_maybe_delete(filename)
        print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
        if st_ut > min(current_ut(), fin_ut):
            print("      Given start time, no data to gather. Exit.")
            return

        # empty ohlcv df
        df = initialize_df()
        while True:
            print(f"      Fetch 1000 pts from {pretty_timestr(st_ut)}")
            exch = self.ss.exchs_dict[exch_str]
            raw_tohlcv_data = safe_fetch_ohlcv(
                exch,
                symbol=pair_str.replace("-", "/"),
                timeframe=self.pp.timeframe,
                since=st_ut,
                limit=1000,
            )
            if raw_tohlcv_data is None:  # exchange had error
                return
            uts = [vec[0] for vec in raw_tohlcv_data]
            if len(uts) > 1:
                # Ideally, time between ohclv candles is always 5m or 1h
                # But exchange data often has gaps. Warn about worst violations
                diffs_ms = np.array(uts[1:]) - np.array(uts[:-1])  # in ms
                diffs_m = diffs_ms / 1000 / 60  # in minutes
                mn_thr = self.pp.timeframe_m * OHLCV_MULT_MIN
                mx_thr = self.pp.timeframe_m * OHLCV_MULT_MAX

                if min(diffs_m) < mn_thr:
                    print(f"      **WARNING: short candle time: {min(diffs_m)} min")
                if max(diffs_m) > mx_thr:
                    print(f"      **WARNING: long candle time: {max(diffs_m)} min")

            # filter out data that's too new
            raw_tohlcv_data = [vec for vec in raw_tohlcv_data if vec[0] <= fin_ut]

            # concat both TOHLCV data
            schema = dict(zip(TOHLCV_COLS, TOHLCV_DTYPES_PL))
            next_df = pl.DataFrame(raw_tohlcv_data, schema=schema)
            df = concat_next_df(df, next_df)

            if len(raw_tohlcv_data) < 1000:  # no more data, we're at newest time
                break

            # prep next iteration
            newest_ut_value = df.tail(1)["timestamp"][0]

            print(f"      newest_ut_value: {newest_ut_value}")
            st_ut = newest_ut_value + self.pp.timeframe_ms

        # add datetime
        df = transform_df(df)

        # output to parquet
        save_parquet(filename, df)

    def _calc_start_ut_maybe_delete(self, filename: str) -> int:
        """
        @description
        Calculate start timestamp, reconciling whether file exists and where
        its data starts. Will delete file if it's inconvenient to re-use

        @arguments
          filename - csv file with data. May or may not exist.

        @return
          start_ut - timestamp (ut) to start grabbing data for
        """
        if not os.path.exists(filename):
            print("      No file exists yet, so will fetch all data")
            return self.ss.st_timestamp

        print("      File already exists")
        if not has_data(filename):
            print("      File has no data, so delete it")
            os.remove(filename)
            return self.ss.st_timestamp

        file_ut0, file_utN = oldest_ut(filename), newest_ut(filename)
        print(f"      File starts at: {pretty_timestr(file_ut0)}")
        print(f"      File finishes at: {pretty_timestr(file_utN)}")

        if self.ss.st_timestamp >= file_ut0:
            print("      User-specified start >= file start, so append file")
            return file_utN + self.pp.timeframe_ms

        print("      User-specified start < file start, so delete file")
        os.remove(filename)
        return self.ss.st_timestamp

    def _load_parquet(self, fin_ut: int) -> Dict[str, Dict[str, pl.DataFrame]]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          parquet_dfs -- dict of [exch_str][pair_str] : df
            Where df has columns=OHLCV_COLS+"datetime", and index=timestamp
        """
        print("  Load parquet.")
        st_ut = self.ss.st_timestamp

        parquet_dfs: Dict[str, Dict[str, pl.DataFrame]] = {}  # [exch][pair] : df
        for exch_str in self.ss.exchange_strs:
            parquet_dfs[exch_str] = {}

        for exch_str, pair_str in self.ss.exchange_pair_tups:
            assert "-" in pair_str, f"pair_str '{pair_str}' needs '-'"
            filename = self._hist_parquet_filename(exch_str, pair_str)
            cols = [
                signal_str  # cols is a subset of TOHLCV_COLS
                for e, signal_str, p in self.ss.input_feed_tups
                if e == exch_str and p == pair_str
            ]
            parquet_df = load_parquet(filename, cols, st_ut, fin_ut)

            assert "datetime" in parquet_df.columns
            assert "timestamp" in parquet_df.columns

            parquet_dfs[exch_str][pair_str] = parquet_df

        return parquet_dfs

    def _merge_parquet_dfs(self, parquet_dfs: dict) -> pl.DataFrame:
        """
        @arguments
          parquet_dfs -- see class docstring

        @return
          hist_df -- see class docstring
        """
        # init hist_df such that it can do basic operations
        print("  Merge parquet DFs.")
        hist_df = initialize_df()
        hist_df_cols = ["timestamp"]
        for exch_str in parquet_dfs.keys():
            for pair_str, parquet_df in parquet_dfs[exch_str].items():
                assert "-" in pair_str, f"pair_s{pair_str}' needs -"
                assert "datetime" in parquet_df.columns
                assert "timestamp" in parquet_df.columns

                for parquet_col in parquet_df.columns:
                    if parquet_col in ["timestamp", "datetime"]:
                        continue

                    signal_str = parquet_col  # eg "close"
                    hist_col = f"{exch_str}:{pair_str}:{signal_str}"

                    parquet_df = parquet_df.with_columns(
                        [pl.col(parquet_col).alias(hist_col)]
                    )
                    hist_df_cols.append(hist_col)

                # drop columns we won't merge
                # drop original OHLCV cols and datetime
                parquet_df = parquet_df.drop(OHLCV_COLS)
                if "datetime" in hist_df.columns:
                    parquet_df = parquet_df.drop("datetime")

                # drop OHLCV from hist_df_cols
                hist_df_cols = [x for x in hist_df_cols if x not in OHLCV_COLS]

                # join to hist_df
                if hist_df.shape[0] == 0:
                    hist_df = parquet_df
                else:
                    hist_df = hist_df.join(parquet_df, on="timestamp", how="outer")

        # select columns in-order [timestamp, ..., datetime]
        hist_df = hist_df.select(hist_df_cols + ["datetime"])

        assert "datetime" in hist_df.columns
        assert "timestamp" in hist_df.columns

        return hist_df

    # TO DO: Move to model_factory/model + use generic df<=>serialize<=>parquet
    def create_xy(
        self,
        hist_df: pl.DataFrame,
        testshift: int,
        do_fill_nans: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray, pd.DataFrame]:
        """
        @arguments
          hist_df -- *polars* DataFrame. See class docstring
          testshift -- to simulate across historical test data
          do_fill_nans -- if any values are nan, fill them? (Via interpolation)
            If you turn this off and hist_df has nans, then X/y/etc gets nans

        @return --
          X -- 2d array of [sample_i, var_i] : value -- inputs for model
          y -- 1d array of [sample_i] -- target outputs for model
          x_df -- *pandas* DataFrame. See class docstring.
        """
        # preconditions
        assert isinstance(hist_df, pl.DataFrame), pl.__class__
        assert "timestamp" in hist_df.columns
        assert "datetime" in hist_df.columns

        # condition inputs
        if do_fill_nans and has_nan(hist_df):
            hist_df = fill_nans(hist_df)
        ss = self.ss

        # main work
        x_df = pd.DataFrame()  # build this up

        target_hist_cols = [
            f"{exch_str}:{pair_str}:{signal_str}"
            for exch_str, signal_str, pair_str in ss.input_feed_tups
        ]

        for hist_col in target_hist_cols:
            assert hist_col in hist_df.columns, f"missing data col: {hist_col}"
            z = hist_df[hist_col].to_list()  # [..., z(t-3), z(t-2), z(t-1)]
            maxshift = testshift + ss.autoregressive_n
            N_train = min(ss.max_n_train, len(z) - maxshift - 1)
            if N_train <= 0:
                print(
                    f"Too little data. len(z)={len(z)}, maxshift={maxshift}"
                    " (= testshift + autoregressive_n = "
                    f"{testshift} + {ss.autoregressive_n})\n"
                    "To fix: broaden time, shrink testshift, "
                    "or shrink autoregressive_n"
                )
                sys.exit(1)
            for delayshift in range(ss.autoregressive_n, 0, -1):  # eg [2, 1, 0]
                shift = testshift + delayshift
                x_col = hist_col + f":t-{delayshift+1}"
                assert (shift + N_train + 1) <= len(z)
                # 1 point for test, the rest for train data
                x_df[x_col] = _slice(z, -shift - N_train - 1, -shift)

        X = x_df.to_numpy()

        # y is set from yval_{exch_str, signal_str, pair_str}
        # eg y = [BinEthC_-1, BinEthC_-2, ..., BinEthC_-450, BinEthC_-451]
        pp = self.pp
        hist_col = f"{pp.exchange_str}:{pp.pair_str}:{pp.signal_str}"
        z = hist_df[hist_col].to_list()
        y = np.array(_slice(z, -testshift - N_train - 1, -testshift))

        # postconditions
        assert X.shape[0] == y.shape[0]
        assert X.shape[0] <= (ss.max_n_train + 1)
        assert X.shape[1] == ss.n
        assert isinstance(x_df, pd.DataFrame)

        # return
        return X, y, x_df

    def _hist_parquet_filename(self, exch_str, pair_str) -> str:
        """
        Given exch_str and pair_str (and self path),
        compute parquet filename
        """
        assert "-" in pair_str, f"pair_str '{pair_str}' needs '-'"
        basename = f"{exch_str}_{pair_str}_{self.pp.timeframe}.parquet"
        filename = os.path.join(self.ss.parquet_dir, basename)
        return filename


@enforce_types
def _slice(x: list, st: int, fin: int) -> list:
    """Python list slice returns an empty list on x[st:fin] if st<0 and fin=0
    This overcomes that issue, for cases when st<0"""
    assert st < 0
    assert fin <= 0
    assert st < fin
    if fin == 0:
        return x[st:]
    return x[st:fin]


@enforce_types
def safe_fetch_ohlcv(
    exch,
    symbol: str,
    timeframe: str,
    since: int,
    limit: int,
) -> Union[List[tuple], None]:
    """
    @description
      calls ccxt.exchange.fetch_ohlcv() but if there's an error it
      emits a warning and returns None, vs crashing everything

    @arguments
      exch -- eg ccxt.binanceus()
      symbol -- eg "BTC/USDT". NOT "BTC-USDT"
      timeframe -- eg "1h", "1m"
      since -- timestamp of first candle. In unix time (in ms)
      limit -- max # candles to retrieve

    @return
      raw_tohlcv_data -- [a TOHLCV tuple, for each timestamp].
        where row 0 is oldest
        and TOHLCV = {unix time (in ms), Open, High, Low, Close, Volume}
    """
    if "-" in symbol:
        raise ValueError(f"Got symbol={symbol}. It must have '/' not '-'")

    try:
        return exch.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            since=since,
            limit=limit,
        )
    except Exception as e:
        print(f"      **WARNING exchange: {e}")
        return None
