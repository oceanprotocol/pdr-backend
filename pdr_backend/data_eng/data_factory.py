import os
import sys
from typing import Dict

from enforce_typing import enforce_types
import numpy as np
import pandas as pd
import polars as pl

from pdr_backend.data_eng.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    OHLCV_MULT_MIN,
    OHLCV_MULT_MAX,
)
from pdr_backend.data_eng.data_pp import DataPP
from pdr_backend.data_eng.data_ss import DataSS
from pdr_backend.data_eng.pdutil import (
    initialize_df,
    transform_df,
    concat_next_df,
    save_csv,
    load_csv,
    save_parquet,
    load_parquet,
    has_data,
    oldest_ut,
    newest_ut,
)
from pdr_backend.util.mathutil import has_nan, fill_nans
from pdr_backend.util.timeutil import pretty_timestr, current_ut


@enforce_types
class DataFactory:
    def __init__(self, pp: DataPP, ss: DataSS):
        self.pp = pp
        self.ss = ss

    def get_hist_df(self) -> pd.DataFrame:
        """
        @description
          Get historical dataframe, across many exchanges & pairs.

        @return
          hist_df -- df w/ cols={exchange_str}:{pair_str}:{signal}+"datetime",
            and index=timestamp
        """
        print("Get historical data, across many exchanges & pairs: begin.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut
        fin_ut = self.ss.fin_timestamp

        print(f"  Data start: {pretty_timestr(self.ss.st_timestamp)}")
        print(f"  Data fin: {pretty_timestr(fin_ut)}")

        self._update_csvs(fin_ut)
        csv_dfs = self._load_csvs(fin_ut)
        hist_df = self._merge_csv_dfs(csv_dfs)

        print("Get historical data, across many exchanges & pairs: done.")
        return hist_df

    def _update_csvs(self, fin_ut: int):
        print("  Update csvs.")
        for exch_str, pair_str in self.ss.exchange_pair_tups:
            self._update_hist_csv_at_exch_and_pair(exch_str, pair_str, fin_ut)

    def _update_hist_csv_at_exch_and_pair(
        self, exch_str: str, pair_str: str, fin_ut: int
    ):
        pair_str = pair_str.replace("/", "-")
        print(f"    Update csv at exchange={exch_str}, pair={pair_str}.")

        filename = self._hist_csv_filename(exch_str, pair_str)
        print(f"      filename={filename}")

        st_ut = self._calc_start_ut_maybe_delete(filename)
        print(f"      Aim to fetch data from start time: {pretty_timestr(st_ut)}")
        if st_ut > min(current_ut(), fin_ut):
            print("      Given start time, no data to gather. Exit.")
            return

        # fill in
        df = initialize_df(OHLCV_COLS)
        while True:
            print(f"      Fetch 1000 pts from {pretty_timestr(st_ut)}")

            exch = self.ss.exchs_dict[exch_str]

            # C is [sample x signal(TOHLCV)]. Row 0 is oldest
            # TOHLCV = unixTime (in ms), Open, High, Low, Close, Volume
            raw_tohlcv_data = exch.fetch_ohlcv(
                symbol=pair_str.replace("-", "/"),  # eg "BTC/USDT"
                timeframe=self.pp.timeframe,  # eg "5m", "1h"
                since=st_ut,  # timestamp of first candle
                limit=1000,  # max # candles to retrieve
            )
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

            raw_tohlcv_data = [vec for vec in raw_tohlcv_data if vec[0] <= fin_ut]
            next_df = pd.DataFrame(raw_tohlcv_data, columns=TOHLCV_COLS)
            df = concat_next_df(df, next_df)

            if len(raw_tohlcv_data) < 1000:  # no more data, we're at newest time
                break

            # prep next iteration
            newest_ut_value = int(df.index.values[-1])
            st_ut = newest_ut_value + self.pp.timeframe_ms

        # output to csv
        save_csv(filename, df)

    def _update_hist_parquet_at_exch_and_pair(
        self, exch_str: str, pair_str: str, fin_ut: int
    ):
        pair_str = pair_str.replace("/", "-")
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

            # C is [sample x signal(TOHLCV)]. Row 0 is oldest
            # TOHLCV = unixTime (in ms), Open, High, Low, Close, Volume
            raw_tohlcv_data = exch.fetch_ohlcv(
                symbol=pair_str.replace("-", "/"),  # eg "BTC/USDT"
                timeframe=self.pp.timeframe,  # eg "5m", "1h"
                since=st_ut,  # timestamp of first candle
                limit=1000,  # max # candles to retrieve
            )
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

            raw_tohlcv_data = [vec for vec in raw_tohlcv_data if vec[0] <= fin_ut]
            next_df = pl.DataFrame(raw_tohlcv_data, schema=TOHLCV_COLS)
            # concat both TOHLCV data
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

    def _load_csvs(self, fin_ut: int) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          csv_dfs -- dict of [exch_str][pair_str] : df
            Where df has columns=OHLCV_COLS+"datetime", and index=timestamp
        """
        print("  Load csvs.")
        st_ut = self.ss.st_timestamp

        csv_dfs: Dict[str, Dict[str, pd.DataFrame]] = {}  # [exch][pair] : df
        for exch_str in self.ss.exchange_strs:
            csv_dfs[exch_str] = {}

        for exch_str, pair_str in self.ss.exchange_pair_tups:
            print(f"Load csv from exchange={exch_str}, pair={pair_str}")
            filename = self._hist_csv_filename(exch_str, pair_str)
            cols = [
                signal_str  # cols is a subset of TOHLCV_COLS
                for e, signal_str, p in self.ss.input_feed_tups
                if e == exch_str and p == pair_str
            ]
            csv_df = load_csv(filename, cols, st_ut, fin_ut)
            assert "datetime" in csv_df.columns
            assert csv_df.index.name == "timestamp"
            csv_dfs[exch_str][pair_str] = csv_df

        return csv_dfs

    def _merge_csv_dfs(self, csv_dfs: dict) -> pd.DataFrame:
        """
        @arguments
          csv_dfs -- dict [exch_str][pair_str] : df
            where df has cols={signal_str}+"datetime", and index=timestamp
        @return
          hist_df -- df w/ cols={exch_str}:{pair_str}:{signal_str}+"datetime",
            and index=timestamp
        """
        print("  Merge csv DFs.")
        hist_df = pd.DataFrame()
        for exch_str in csv_dfs.keys():
            for pair_str, csv_df in csv_dfs[exch_str].items():
                assert "-" in pair_str, pair_str
                assert "datetime" in csv_df.columns
                assert csv_df.index.name == "timestamp"

                for csv_col in csv_df.columns:
                    if csv_col == "datetime":
                        if "datetime" in hist_df.columns:
                            continue
                        hist_col = csv_col
                    else:
                        signal_str = csv_col  # eg "close"
                        hist_col = f"{exch_str}:{pair_str}:{signal_str}"
                    hist_df[hist_col] = csv_df[csv_col]

        assert "datetime" in hist_df.columns
        assert hist_df.index.name == "timestamp"
        return hist_df

    def create_xy(
        self,
        hist_df: pd.DataFrame,
        testshift: int,
        do_fill_nans: bool = True,
    ):
        """
        @arguments
          hist_df -- df w cols={exch_str}:{pair_str}:{signal_str}+"datetime",
            and index=timestamp
          testshift -- to simulate across historical test data
          do_fill_nans -- if any values are nan, fill them? (Via interpolation)
            If you turn this off and hist_df has nans, then X/y/etc gets nans

        @return --
          X -- 2d array of [sample_i, var_i] : value
          y -- 1d array of [sample_i]
          x_df -- df w/ cols={exch_str}:{pair_str}:{signal}:t-{x} + "datetime"
            index=0,1,.. (nothing special)
        """
        if do_fill_nans and has_nan(hist_df):
            hist_df = fill_nans(hist_df)

        ss = self.ss
        x_df = pd.DataFrame()

        target_hist_cols = [
            f"{exch_str}:{pair_str}:{signal_str}"
            for exch_str, signal_str, pair_str in ss.input_feed_tups
        ]

        for hist_col in target_hist_cols:
            assert hist_col in hist_df.columns, "missing a data col"
            z = hist_df[hist_col].tolist()  # [..., z(t-3), z(t-2), z(t-1)]
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
        z = hist_df[hist_col].tolist()
        y = np.array(_slice(z, -testshift - N_train - 1, -testshift))

        # postconditions
        assert X.shape[0] == y.shape[0]
        assert X.shape[0] <= (ss.max_n_train + 1)
        assert X.shape[1] == ss.n

        # return
        return X, y, x_df

    def _hist_csv_filename(self, exch_str, pair_str) -> str:
        """
        Given exch_str and pair_str (and self path),
        compute csv filename
        """
        pair_str = pair_str.replace("/", "-")
        basename = f"{exch_str}_{pair_str}_{self.pp.timeframe}.csv"
        filename = os.path.join(self.ss.csv_dir, basename)
        return filename

    def _hist_parquet_filename(self, exch_str, pair_str) -> str:
        """
        Given exch_str and pair_str (and self path),
        compute parquet filename
        """
        pair_str = pair_str.replace("/", "-")
        basename = f"{exch_str}_{pair_str}_{self.pp.timeframe}.parquet"
        filename = os.path.join(self.ss.csv_dir, basename)
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
