import polars as pl
from typing import List

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.analytics.predictoor_stats import get_feed_summary_stats_lazy
from pdr_backend.lake.plutil import check_df_len

@enforce_types
def get_predictions_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, feed_addrs: List[str]
):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    predictions_df = gql_dfs["pdr_predictions"]
    assert (
        predictions_df is not None and len(predictions_df) > 0
    ), "Lake has no predictions."

    lazy_df = predictions_df.lazy()
    # filter by feed addresses
    if feed_addrs:
        feed_addrs = [f.lower() for f in feed_addrs]

        lazy_df = lazy_df.filter(
            pl.col("ID")
            .apply(lambda x: x.split("-")[0], return_dtype=pl.Utf8)
            .is_in(feed_addrs)
        )

    # filter by start and end dates
    lazy_df = lazy_df.filter(
        pl.col("timestamp").is_between(
            timestr_to_ut(start_timestr) / 1000, timestr_to_ut(end_timestr) / 1000
        )
    )

    check_df_len(
        lazy_df=lazy_df,
        max_len=None,
        min_len=None,
        identifier="predictions_df"
    )

    lazy_feed_summary_df = get_feed_summary_stats_lazy(lazy_df)

    feed_summary_df = lazy_feed_summary_df.collect()

    print(feed_summary_df)
