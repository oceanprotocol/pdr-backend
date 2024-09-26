import logging
from typing import Union, Optional, Any
from datetime import datetime, timezone
import os
import time
import polars as pl
from enforce_typing import enforce_types
import duckdb

logger = logging.getLogger("duckDB_file_reader")


class DuckDBFileReader:
    def __init__(self, files_dir, seconds_between_caches):
        self.files_dir = files_dir
        self.seconds_between_caches = seconds_between_caches
        self.start_date: Optional[datetime] = None

    def set_start_date(self, start_dt: Optional[datetime]):
        self.start_date = start_dt

    def _is_cache_valid(
        self, cache_file_path: str, seconds_between_caches: int
    ) -> bool:
        """Checks if the cache file exists and is within the valid time limit."""
        if os.path.exists(cache_file_path):
            file_age = time.time() - os.path.getmtime(cache_file_path)
            return file_age < seconds_between_caches
        return False

    def _run_query_and_cache(self, cache_file_path: str, query: str):
        """Runs the query and caches the result in a parquet file."""
        duckdb.execute(f"COPY ({query}) TO '{cache_file_path}' (FORMAT 'parquet')")

    def _fetch_query_result(self, query: str, scalar: bool):
        """Fetches the query result, either from cache or the database."""
        if scalar:
            result = duckdb.execute(query).fetchone()
            return result[0] if result and len(result) == 1 else result
        return duckdb.execute(query).pl()

    @enforce_types
    def _check_cache_query_data(
        self, query: str, cache_file_name: str, scalar: bool
    ) -> Union[Any, pl.DataFrame, None]:
        """
        Executes a query and caches the result in a parquet file for up to an hour.
        If a cached file exists and is less than an hour old, the cached result is used.

        Args:
            query: SQL query to execute.
            cache_file_name: Name of the cache file (without extension).
            scalar: Boolean flag indicating if the result should be a scalar.

        Returns:
            Query result as a list of dictionaries (for scalar=False)
            or a scalar value (for scalar=True),
            or None if the query execution fails.
        """
        cache_file_dir = os.path.join(self.files_dir, "exports", "cache")
        cache_file_path = os.path.join(cache_file_dir, f"{cache_file_name}.parquet")

        os.makedirs(cache_file_dir, exist_ok=True)
        # If the cache is valid, use it; otherwise, re-run the query and cache the results
        if self._is_cache_valid(cache_file_path, self.seconds_between_caches):
            query = f"SELECT * FROM '{cache_file_path}'"
        else:
            self._run_query_and_cache(cache_file_path, query)

        # Fetch and return the query result
        return self._fetch_query_result(query, scalar)

    @enforce_types
    def _query_db(
        self, query: str, scalar=False, cache_file_name=None, periodical=True
    ) -> Union[Any, pl.DataFrame]:
        """
        Query the database with the given query.
        Args:
            query (str): SQL query.
        Returns:
            dict: Query result.
        """
        try:
            if cache_file_name:
                if periodical:
                    period_days = (
                        (datetime.now(tz=timezone.utc) - self.start_date).days
                        if self.start_date
                        else 0
                    )
                    cache_file_name = f"{cache_file_name}_{period_days}_days"
                cache_data = self._check_cache_query_data(
                    query, cache_file_name, scalar
                )
                return cache_data

            # If scalar, fetch a single result
            if scalar:
                result = duckdb.execute(query).fetchone()
                return result[0] if result and len(result) == 1 else result

            return duckdb.execute(query).pl()
        except Exception as e:
            logger.error("Error querying the database: %s", e)
            return pl.DataFrame()
