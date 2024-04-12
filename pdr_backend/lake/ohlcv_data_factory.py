import logging
import os
from typing import Dict

import polars as pl
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_timeframe import ArgTimeframe
from pdr_backend.lake.constants import (
    TOHLCV_SCHEMA_PL,
)
from pdr_backend.lake.fetch_ohlcv import clean_raw_ohlcv, safe_fetch_ohlcv_ccxt
from pdr_backend.lake.merge_df import merge_rawohlcv_dfs
from pdr_backend.lake.plutil import concat_next_df, initialize_rawohlcv_df
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.util.time_types import UnixTimeMs
from pdr_backend.lake.csv_data_store import CSVDataStore

logger = logging.getLogger("ohlcv_data_factory")


@enforce_types
class OhlcvDataFactory:
    """
    Roles:
    - From each CEX API, fill >=1 rawohlcv_dfs -> rawohlcv files data lake
    - From rawohlcv_dfs, fill 1 mergedohlcv_df -- all data across all CEXes

    Where:
      rawohlcv_dfs -- dict of [exch_str][pair_str] : df
        And df has columns of: "timestamp", "open", "high", .., "volume"
        And NOT "datetime" column
        Where pair_str must have '/' not '-', to avoid key issues


      mergedohlcv_df -- polars DataFrame with cols like:
        "timestamp",
        "binanceus:ETH-USDT:open",
        "binanceus:ETH-USDT:high",
        "binanceus:ETH-USDT:low",
        "binanceus:ETH-USDT:close",
        "binanceus:ETH-USDT:volume",
        ...
       (NOT "datetime")

      #For each column: oldest first, newest at the end

    Finally:
       - "timestamp" values are ut: int is unix time, UTC, in ms (not s)
    """

    def __init__(self, ss: LakeSS):
        self.ss = ss

    def get_mergedohlcv_df(self) -> pl.DataFrame:
        """
        @description
          Get dataframe of all ohlcv data: merged from many exchanges & pairs.

        @return
          mergedohlcv_df -- *polars* Dataframe. See class docstring
        """
        logger.info("Get historical data, across many exchanges & pairs: begin.")

        # Ss_timestamp is calculated dynamically if ss.fin_timestr = "now".
        # But, we don't want fin_timestamp changing as we gather data here.
        # To solve, for a given call to this method, we make a constant fin_ut
        fin_ut = self.ss.fin_timestamp

        logger.info("Data start: %s", self.ss.st_timestamp.pretty_timestr())
        logger.info("Data fin: %s", fin_ut.pretty_timestr())

        # fetch new data and write to csv files
        self._update_rawohlcv_files(fin_ut)

        # load from rawohlcv csv files into raw ohlcv_dfs
        rawohlcv_dfs = self._load_rawohlcv_files(fin_ut)

        # Merge all DataFrames into a single DataFrame
        mergedohlcv_df = merge_rawohlcv_dfs(rawohlcv_dfs)

        # postconditions
        assert isinstance(
            mergedohlcv_df, pl.DataFrame
        ), "mergedohlcv_df is not a pl.DataFrame"

        logger.info("Get historical data, across many exchanges & pairs: done.")
        return mergedohlcv_df

    def _update_rawohlcv_files(self, fin_ut: UnixTimeMs):
        logger.info("Update all rawohlcv files: begin")
        for feed in self.ss.feeds:
            self._update_rawohlcv_files_at_feed(feed, fin_ut)

        logger.info("Update all rawohlcv files: done")

    def _update_rawohlcv_files_at_feed(self, feed: ArgFeed, fin_ut: UnixTimeMs):
        """
        @arguments
          feed -- ArgFeed
          fin_ut -- a timestamp, in ms, in UTC
        """
        pair_str = str(feed.pair)
        exch_str = str(feed.exchange)
        assert "/" in str(pair_str), f"pair_str={pair_str} needs '/'"

        logger.info(
            "Update rawohlcv file at exchange=%s, pair=%s: begin", exch_str, pair_str
        )

        dataset_identifier = self.get_dataset_identifier(feed)
        logger.info("dataset_identifier=%s", dataset_identifier)

        assert feed.timeframe
        st_ut = self._calc_start_ut_maybe_delete(feed.timeframe, dataset_identifier)
        logger.info("Aim to fetch data from start time: %s", st_ut.pretty_timestr())
        if st_ut > min(UnixTimeMs.now(), fin_ut):
            logger.info("Given start time, no data to gather. Exit.")
            return

        # empty ohlcv df
        df = initialize_rawohlcv_df()
        while True:
            limit = 1000
            logger.info("Fetch up to %s pts from %s", limit, st_ut.pretty_timestr())
            exch = feed.ccxt_exchange()
            raw_tohlcv_data = safe_fetch_ohlcv_ccxt(
                exch,
                symbol=str(pair_str).replace("-", "/"),
                timeframe=str(feed.timeframe),
                since=st_ut,
                limit=limit,
            )
            tohlcv_data = clean_raw_ohlcv(raw_tohlcv_data, feed, st_ut, fin_ut)

            # concat both TOHLCV data
            next_df = pl.DataFrame(tohlcv_data, schema=TOHLCV_SCHEMA_PL)
            df = concat_next_df(df, next_df)

            if len(tohlcv_data) < limit:  # no more data, we're at newest time
                break

            # prep next iteration
            newest_ut_value = df.tail(1)["timestamp"][0]

            logger.debug("newest_ut_value: %s", newest_ut_value)
            st_ut = UnixTimeMs(newest_ut_value + feed.timeframe.ms)

        # output to file
        CSVDataStore(self.ss.lake_dir).write(
            dataset_identifier=dataset_identifier, data=df, schema=TOHLCV_SCHEMA_PL
        )

        # done
        logger.info(
            "Update rawohlcv file at exchange=%s, pair=%s: done", exch_str, pair_str
        )

    def _calc_start_ut_maybe_delete(
        self, timeframe: ArgTimeframe, dataset_identifier: str
    ) -> UnixTimeMs:
        """
        @description
        Calculate start timestamp, reconciling whether file exists and where
        its data starts. Will delete file if it's inconvenient to re-use

        @arguments
          timeframe - Timeframe
          dataset_identifier - csv file with data. May or may not exist.

        @return
          start_ut - timestamp (ut) to start grabbing data for
        """
        cds = CSVDataStore(self.ss.lake_dir)
        if not cds.get_folder_exists(dataset_identifier):
            logger.info("No file exists yet, so will fetch all data")
            return UnixTimeMs(self.ss.st_timestamp)

        logger.info("File already exists")
        if not cds.has_data(dataset_identifier):
            logger.info("File has no data, so delete it")
            cds.truncate(dataset_identifier)
            return UnixTimeMs(self.ss.st_timestamp)

        file_ut0, file_utN = cds.get_first_timestamp(
            dataset_identifier
        ), cds.get_last_timestamp(dataset_identifier)

        logger.info("File starts at: %s", file_ut0.pretty_timestr())
        logger.info("File finishes at: %s", file_utN.pretty_timestr())

        if self.ss.st_timestamp >= file_ut0:
            logger.info("User-specified start >= file start, so append file")
            return UnixTimeMs(file_utN + timeframe.ms)

        logger.info("User-specified start < file start, so delete file")
        cds.truncate(dataset_identifier)
        return UnixTimeMs(self.ss.st_timestamp)

    def _load_rawohlcv_files(self, fin_ut: int) -> Dict[str, Dict[str, pl.DataFrame]]:
        """
        @arguments
          fin_ut -- finish timestamp

        @return
          rawohlcv_dfs -- dict of [exch_str][pair_str] : ohlcv_df
            Where df has columns: TOHLCV_COLS
            And pair_str is eg "BTC/USDT", *not* "BTC-USDT"
        """
        logger.info("Load rawohlcv file.")
        st_ut = self.ss.st_timestamp

        rawohlcv_dfs: Dict[str, Dict[str, pl.DataFrame]] = {}  # [exch][pair] : df
        for exch_str in self.ss.exchange_strs:
            rawohlcv_dfs[exch_str] = {}

        for feed in self.ss.feeds:
            pair_str = str(feed.pair)
            exch_str = str(feed.exchange)
            assert "/" in str(pair_str), f"pair_str={pair_str} needs '/'"
            dataset_identifier = self.get_dataset_identifier(feed)
            rawohlcv_df = CSVDataStore(self.ss.lake_dir).read(
                dataset_identifier, st_ut, fin_ut, TOHLCV_SCHEMA_PL
            )

            assert "timestamp" in rawohlcv_df.columns
            assert "datetime" not in rawohlcv_df.columns

            rawohlcv_dfs[exch_str][pair_str] = rawohlcv_df

        # rawohlcv_dfs["kraken"] is a DF, with proper cols, and 0 rows

        return rawohlcv_dfs

    def _rawohlcv_filename(self, feed: ArgFeed) -> str:
        """
        @description
          Computes a filename for the rawohlcv data.

        @arguments
          feed -- ArgFeed

        @return
          rawohlcv_filename --

        @notes
          If pair_str has '/', it will become '-' in the filename.
        """
        pair_str = str(feed.pair)
        assert "/" in str(pair_str) or "-" in pair_str, pair_str
        pair_str = str(pair_str).replace("/", "-")  # filesystem needs "-"
        basename = f"{feed.exchange}_{pair_str}_{feed.timeframe}.parquet"
        filename = os.path.join(self.ss.lake_dir, basename)
        return filename

    def get_dataset_identifier(self, feed: ArgFeed) -> str:
        """
        @description
          Get a unique identifier for the dataset that this factory is working with.
          This is useful for identifying the dataset in the database.

        @return
          dataset_identifier -- str
        """
        pair_str = str(feed.pair)
        assert "/" in str(pair_str) or "-" in pair_str, pair_str
        pair_str = str(pair_str).replace("/", "-")  # filesystem needs "-"
        return f"{feed.exchange}_{pair_str}_{feed.timeframe}"
