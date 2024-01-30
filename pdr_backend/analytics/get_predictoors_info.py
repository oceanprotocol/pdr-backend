from typing import Union
import polars as pl

from enforce_typing import enforce_types
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.analytics.predictoor_stats import get_predictoor_summary_stats_lazy
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.timeutil import timestr_to_ut


@enforce_types
def get_predictoors_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, pdr_addrs_str: Union[str, None]
):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    if len(gql_dfs) == 0:
        print("No records found. Please adjust start and end times.")
        return
    predictions_df = gql_dfs["pdr_predictions"]

    lazy_df = predictions_df.lazy()
    # filter by user addresses
    if pdr_addrs_str:
        pdr_addrs_list = pdr_addrs_str.lower().split(",")
        lazy_df = lazy_df.filter(
            predictions_df["user"].is_in(pdr_addrs_list)
        )

    # filter by start and end dates
    lazy_df = lazy_df.filter(
        pl.col("timestamp").is_between(
            timestr_to_ut(start_timestr) / 1000, timestr_to_ut(end_timestr) / 1000
        )
    )

    lazy_predictoor_summary_df = get_predictoor_summary_stats_lazy(lazy_df)

    predictoor_summary_df = lazy_predictoor_summary_df.collect()
    print(predictoor_summary_df)
