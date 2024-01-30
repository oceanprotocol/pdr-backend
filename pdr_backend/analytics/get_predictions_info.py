from typing import Union
import polars as pl

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.analytics.predictoor_stats import get_feed_summary_stats_lazy

@enforce_types
def get_predictions_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, feed_addrs_str: Union[str, None]
):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    if len(gql_dfs["pdr_predictions"]) == 0:
        print("No records found. Please adjust start and end times.")
        return
    predictions_df = gql_dfs["pdr_predictions"]

    lazy_df = predictions_df.lazy()
    # filter by feed addresses
    if feed_addrs_str:
        feed_addrs_list = feed_addrs_str.lower().split(",")
        lazy_df = lazy_df.filter(
            pl.col("ID")
            .apply(lambda x: x.split("-")[0], return_dtype=pl.Utf8)
            .is_in(feed_addrs_list)
        )

    # filter by start and end dates
    lazy_df = lazy_df.filter(
        pl.col("timestamp").is_between(
            timestr_to_ut(start_timestr) / 1000, timestr_to_ut(end_timestr) / 1000
        )
    )

    lazy_feed_summary_df = get_feed_summary_stats_lazy(lazy_df)

    feed_summary_df = lazy_feed_summary_df.collect()
    print(feed_summary_df)
