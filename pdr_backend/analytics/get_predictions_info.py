#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import List

from enforce_typing import enforce_types

from pdr_backend.analytics.predictoor_stats import (
    get_feed_summary_stats,
    get_predictoor_summary_stats,
    get_slot_statistics,
    get_traction_statistics,
    plot_slot_daily_statistics,
    plot_traction_cum_sum_statistics,
    plot_traction_daily_statistics,
)
from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.table import Table
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("get_predictions_info")


@enforce_types
def _address_list_to_str(addresses: List[str]) -> str:
    return "(" + ", ".join([f"'{f.lower()}'" for f in addresses]) + ")"


@enforce_types
def _checks_for_empty_df(df, table_name: str):
    assert df is not None, f"No table found: {table_name}"
    assert len(df) > 0, "No records to summarize. Please adjust params."


@enforce_types
def get_predictions_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, feed_addrs: List[str]
):
    logger.info(
        "get_predictions_info_main_ppss.lake_ss.lake_dir--- %s", ppss.lake_ss.lake_dir
    )
    logger.info("get_predictions_info_main start_timestr %s", start_timestr)
    logger.info("get_predictions_info_main end_timestr %s", end_timestr)

    table_name = Table("pdr_predictions").table_name

    # convert feed addresses to string for SQL query
    feed_addrs_str = _address_list_to_str(feed_addrs)

    query = f"""
        SELECT *,
        FROM {table_name}
        WHERE
            timestamp >= {UnixTimeMs.from_timestr(start_timestr)}
            AND timestamp <= {UnixTimeMs.from_timestr(end_timestr)}
            AND contract IN {feed_addrs_str}
    """

    predictions_df = DuckDBDataStore(ppss.lake_ss.lake_dir).query_data(query)

    _checks_for_empty_df(predictions_df, table_name)

    feed_summary_df = get_feed_summary_stats(predictions_df)
    logger.info(feed_summary_df)


@enforce_types
def get_predictoors_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, pdr_addrs: List[str]
):
    logger.info(
        "get_predictoors_info_main_ppss.lake_ss.lake_dir--- %s", ppss.lake_ss.lake_dir
    )
    table_name = Table("pdr_predictions").table_name

    # convert feed addresses to string for SQL query
    pdr_addrs_str = _address_list_to_str(pdr_addrs)

    query = f"""
        SELECT *,
        FROM {table_name}
        WHERE
            timestamp >= {UnixTimeMs.from_timestr(start_timestr)}
            AND timestamp <= {UnixTimeMs.from_timestr(end_timestr)}
            AND user IN {pdr_addrs_str}
    """

    predictions_df = DuckDBDataStore(ppss.lake_ss.lake_dir).query_data(query)

    _checks_for_empty_df(predictions_df, table_name)

    predictoor_summary_df = get_predictoor_summary_stats(predictions_df)
    logger.info(predictoor_summary_df)


@enforce_types
def get_traction_info_main(ppss: PPSS, start_timestr: str, end_timestr: str):
    table_name = Table("pdr_predictions").table_name

    query = f"""
        SELECT *,
        FROM {table_name}
        WHERE
            timestamp >= {UnixTimeMs.from_timestr(start_timestr)}
            AND timestamp <= {UnixTimeMs.from_timestr(end_timestr)}
    """

    predictions_df = DuckDBDataStore(ppss.lake_ss.lake_dir).query_data(query)

    _checks_for_empty_df(predictions_df, table_name)

    # calculate predictoor traction statistics and draw plots
    stats_df = get_traction_statistics(predictions_df)
    plot_traction_cum_sum_statistics(stats_df, ppss.lake_ss.lake_dir)
    plot_traction_daily_statistics(stats_df, ppss.lake_ss.lake_dir)

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions_df)
    plot_slot_daily_statistics(slots_df, ppss.lake_ss.lake_dir)
