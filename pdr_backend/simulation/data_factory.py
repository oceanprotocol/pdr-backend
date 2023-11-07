import os
import sys
from typing import Dict

from enforce_typing import enforce_types
import numpy as np
import pandas as pd

from pdr_backend.simulation.tradeutil import pairstr

from pdr_backend.simulation.constants import (
    OHLCV_COLS,
    TOHLCV_COLS,
    MS_PER_EPOCH,
)
from pdr_backend.simulation.data_ss import DataSS
from pdr_backend.simulation.pdutil import (
    initialize_df,
    concat_next_df,
    save_csv,
    load_csv,
    has_data,
    oldest_ut,
    newest_ut,
)
from pdr_backend.simulation.timeutil import (
    pretty_timestr,
    current_ut,
)


@enforce_types
class DataFactory:
    def __init__(self, ss: DataSS):
        self.ss = ss

    def get_hist_df(self) -> pd.DataFrame:
        """
        @return
          hist_df -- df w/ cols={exchange_id}:{coin}:{signal}+"datetime",
            and index=timestamp
        """
        self._update_csvs()
        csv_dfs = self._load_csvs()
        hist_df = self._merge_csv_dfs(csv_dfs)
        return hist_df

    def _update_csvs(self):
        print("Update csvs.")
        print(f"-User-specified start: {pretty_timestr(self.ss.st_timestamp)}")
        print(f"-User-specified fin: {pretty_timestr(self.ss.fin_timestamp)}")

        for exchange_id in self.ss.exchange_ids:
            for coin in self.ss.coins:
                pair = pairstr(coin, usdcoin=self.ss.usdcoin)
                self._update_hist_csv_at_exch_and_pair(exchange_id, pair)

    def _update_hist_csv_at_exch_and_pair(self, exchange_id, pair):
        print(f"Update csv at exchange={exchange_id}, pair={pair}")

        filename = self._hist_csv_filename(exchange_id, pair)
        print(f"  filename={filename}")

        st_ut = self._calc_start_ut_maybe_delete(filename)
        print(f"  Aim to fetch data from start time: {pretty_timestr(st_ut)}")
        if st_ut > min(current_ut(), self.ss.fin_timestamp):
            print("  Given start time, no data to gather. Exit.")
            return

        # Fill in df
        df = initialize_df(OHLCV_COLS)
        while True:
            print(f"  Fetch 1000 pts from {pretty_timestr(st_ut)}")

            exch = self.ss.exchs_dict[exchange_id]

            # C is [sample x signal(TOHLCV)]. Row 0 is oldest
            # TOHLCV = unixTime (in ms), Open, High, Low, Close, Volume
            raw_tohlcv_data = exch.fetch_ohlcv(
                symbol=pair,
                timeframe=self.ss.timeframe,
                since=st_ut,
                limit=1000,
            )
            uts = [vec[0] for vec in raw_tohlcv_data]
            if len(uts) > 1:
                diffs = np.array(uts[1:]) - np.array(uts[:-1])
                mx, mn = max(diffs), min(diffs)
                diffs_ok = mn == mx == MS_PER_EPOCH
                if not diffs_ok:
                    print(f"**WARNING: diffs not ok: mn={mn}, mx={mx}**")
                # assert mx == mn == MS_PER_EPOCH
            raw_tohlcv_data = [
                vec for vec in raw_tohlcv_data if vec[0] <= self.ss.fin_timestamp
            ]
            next_df = pd.DataFrame(raw_tohlcv_data, columns=TOHLCV_COLS)
            df = concat_next_df(df, next_df)

            if len(raw_tohlcv_data) < 1000:  # no more data, we're at newest time
                break

            # prep next iteration
            newest_ut_value = int(df.index.values[-1])
            # prev_st_ut = st_ut
            st_ut = newest_ut_value + MS_PER_EPOCH

        # output to csv
        save_csv(filename, df)

    def _calc_start_ut_maybe_delete(self, filename: str) -> int:
        """Calculate start timestamp, reconciling whether file exists and where
        its data starts. Will delete file if it's inconvenient to re-use"""
        if not os.path.exists(filename):
            print("  No file exists yet, so will fetch all data")
            return self.ss.st_timestamp

        print("  File already exists")
        if not has_data(filename):
            print("  File has no data, so delete it")
            os.remove(filename)
            return self.ss.st_timestamp

        file_ut0, file_utN = oldest_ut(filename), newest_ut(filename)
        print(f"  File starts at: {pretty_timestr(file_ut0)}")
        print(f"  File finishes at: {pretty_timestr(file_utN)}")

        if self.ss.st_timestamp >= file_ut0:
            print("  User-specified start >= file start, so append file")
            return file_utN + MS_PER_EPOCH

        print("  User-specified start < file start, so delete file")
        os.remove(filename)
        return self.ss.st_timestamp

    def _load_csvs(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        @return -- csv_dfs -- dict of [exchange_id_str][coin_str] : df
          df has columns=OHLCV_COLS+"datetime", and index=timestamp
        """
        cols = self.ss.signals  # subset of TOHLCV_COLS
        st, fin = self.ss.st_timestamp, self.ss.fin_timestamp

        csv_dfs: Dict[str, Dict[str, pd.DataFrame]] = {}
        for exchange_id in self.ss.exchange_ids:
            exch = self.ss.exchs_dict[exchange_id]
            csv_dfs[exchange_id] = {}
            for coin in self.ss.coins:
                pair = pairstr(coin, usdcoin=self.ss.usdcoin)
                print(f"Load csv from exchange={exch}, pair={pair}")
                filename = self._hist_csv_filename(exchange_id, pair)
                csv_df = load_csv(filename, cols, st, fin)
                assert "datetime" in csv_df.columns
                assert csv_df.index.name == "timestamp"
                csv_dfs[exchange_id][coin] = csv_df
        return csv_dfs

    def _merge_csv_dfs(self, csv_dfs: dict) -> pd.DataFrame:
        """
        @arguments
          csv_dfs -- dict [exchange_id][coin] : df
            where df has cols={signal}+"datetime", and index=timestamp
        @return
          hist_df -- df w/ cols={exchange_id}:{coin}:{signal}+"datetime",
            and index=timestamp
        """
        hist_df = pd.DataFrame()
        for exchange_id in csv_dfs.keys():
            for coin, csv_df in csv_dfs[exchange_id].items():
                assert "datetime" in csv_df.columns
                assert csv_df.index.name == "timestamp"

                for csv_col in csv_df.columns:
                    if csv_col == "datetime":
                        if "datetime" in hist_df.columns:
                            continue
                        hist_col = csv_col
                    else:
                        signal = csv_col  # eg "close"
                        hist_col = f"{exchange_id}:{coin}:{signal}"
                    hist_df[hist_col] = csv_df[csv_col]

        assert "datetime" in hist_df.columns
        assert hist_df.index.name == "timestamp"
        return hist_df

    def create_xy(self, hist_df: pd.DataFrame, testshift: int):
        """
        @arguments
          hist_df -- df w/ cols={exchange_id}:{coin}:{signal}+"datetime",
            and index=timestamp
          testshift -- to simulate across historical test data

        @return --
          X -- 2d array of [sample_i, var_i] : value
          y -- 1d array of [sample_i]
          var_with_prev -- int
          x_df -- df w/ cols={exchange_id}:{coin}:{signal}:t-{x} + "datetime"
            index=0,1,.. (nothing special)
        """
        ss = self.ss
        x_df = pd.DataFrame()

        target_hist_cols = [
            f"{exchange_id}:{coin}:{signal}"
            for exchange_id in ss.exchange_ids
            for coin in ss.coins
            for signal in ss.signals
        ]

        for hist_col in target_hist_cols:
            assert hist_col in hist_df.columns, "missing a data col"
            z = hist_df[hist_col].tolist()  # [..., z(t-3), z(t-2), z(t-1)]
            maxshift = testshift + ss.Nt
            N_train = min(ss.max_N_train, len(z) - maxshift - 1)
            if N_train <= 0:
                print(
                    f"Too little data. len(z)={len(z)}, maxshift={maxshift}"
                    f" (= testshift + Nt = {testshift} + {ss.Nt})"
                )
                print("To fix: broaden time, shrink testshift, or shrink Nt")
                sys.exit(1)
            for delayshift in range(ss.Nt, 0, -1):  # eg [2, 1, 0]
                shift = testshift + delayshift
                x_col = hist_col + f":t-{delayshift+1}"
                assert (shift + N_train + 1) <= len(z)
                # 1 point for test, the rest for train data
                x_df[x_col] = _slice(z, -shift - N_train - 1, -shift)

        X = x_df.to_numpy()

        x_cols = x_df.columns.tolist()
        x_col_with_prev = (
            f"{ss.yval_exchange_id}:{ss.yval_coin}:" f"{ss.yval_signal}:t-2"
        )
        var_with_prev = x_cols.index(x_col_with_prev)

        # y is set from yval_{exchange_id, coin, signal}
        # eg y = [BinEthC_-1, BinEthC_-2, ..., BinEthC_-450, BinEthC_-451]
        hist_col = f"{ss.yval_exchange_id}:{ss.yval_coin}:{ss.yval_signal}"
        z = hist_df[hist_col].tolist()
        y = np.array(_slice(z, -testshift - N_train - 1, -testshift))

        # postconditions
        assert X.shape[0] == y.shape[0]
        assert X.shape[0] <= (ss.max_N_train + 1)
        assert X.shape[1] == ss.n

        # return
        return X, y, var_with_prev, x_df

    def _hist_csv_filename(self, exchange_id, pair) -> str:
        """Given exchange_id and pair (and self path), compute csv filename"""
        basename = (
            exchange_id
            + "_"
            + pair.replace("/", "-")
            + "_"
            + self.ss.timeframe
            + ".csv"
        )
        filename = os.path.join(self.ss.csv_dir, basename)
        return filename


def _slice(x: list, st: int, fin: int) -> list:
    """Python list slice returns an empty list on x[st:fin] if st<0 and fin=0
    This overcomes that issue, for cases when st<0"""
    assert st < 0
    assert fin <= 0
    assert st < fin
    if fin == 0:
        return x[st:]
    return x[st:fin]
