"""This module currently gives traction wrt predictoors.
At some point, we can expand it into traction info wrt traders & txs too.
"""

from enforce_typing import enforce_types
import polars as pl

from pdr_backend.analytics.predictoor_stats import (
    get_slot_statistics,
    get_traction_statistics,
    plot_slot_daily_statistics,
    plot_traction_cum_sum_statistics,
    plot_traction_daily_statistics,
)
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def get_traction_info_main(ppss: PPSS, start_timestr: str, end_timestr: str):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    predictions_df = gql_dfs["pdr_predictions"]
    assert (
        predictions_df is not None and len(predictions_df) > 0
    ), "Lake has no predictions."

    lazy_df = predictions_df.lazy()
    # filter by start and end dates
    lazy_df = lazy_df.filter(
        pl.col("timestamp").is_between(
            timestr_to_ut(start_timestr), timestr_to_ut(end_timestr)
        )
    )

    predictions_df = lazy_df.collect()
    if predictions_df.shape[0] == 0:
        print("No records found. Please adjust start and end times params.")
        return

    # calculate predictoor traction statistics and draw plots
    stats_df = get_traction_statistics(predictions_df)
    plot_traction_cum_sum_statistics(stats_df, ppss.lake_ss.parquet_dir)
    plot_traction_daily_statistics(stats_df, ppss.lake_ss.parquet_dir)

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions_df)
    plot_slot_daily_statistics(slots_df, ppss.lake_ss.parquet_dir)
