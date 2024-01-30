import polars as pl
from typing import List, Union

from enforce_typing import enforce_types
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.analytics.predictoor_stats import get_predictoor_summary_stats_lazy
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.timeutil import timestr_to_ut
from pdr_backend.lake.plutil import check_df_len

@enforce_types
def get_predictoors_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, pdr_addrs: List[str]
):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    predictions_df = gql_dfs["pdr_predictions"]
    assert (
        predictions_df is not None and len(predictions_df) > 0
    ), "Lake has no predictions."

    lazy_df = predictions_df.lazy()
    # filter by user addresses

    if len(pdr_addrs) > 0:
        pdr_addrs = [f.lower() for f in pdr_addrs]
        lazy_df = lazy_df.filter(
            pl.col("user").is_in(pdr_addrs)
        )

    # filter by start and end dates
    lazy_df = lazy_df.filter(
        pl.col("timestamp").is_between(
            timestr_to_ut(start_timestr), timestr_to_ut(end_timestr)
        )
    )

    check_df_len(
        lazy_df=lazy_df,
        max_len=None,
        min_len=None,
        identifier="predictions_df"
    )

    lazy_predictoor_summary_df = get_predictoor_summary_stats_lazy(lazy_df)
    predictoor_summary_df = lazy_predictoor_summary_df.collect()
    print(predictoor_summary_df)
