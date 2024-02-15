import logging
from typing import List

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.analytics.predictoor_stats import (
    get_feed_summary_stats,
    get_predictoor_summary_stats,
    get_slot_statistics,
    get_traction_statistics,
    plot_slot_daily_statistics,
    plot_traction_cum_sum_statistics,
    plot_traction_daily_statistics,
)
from pdr_backend.util.timeutil import timestr_to_ut

logger = logging.getLogger("get_predictions_info")


class PredFilter:
    def __init__(self, ppss):
        gql_data_factory = GQLDataFactory(ppss)
        gql_dfs = gql_data_factory.get_gql_dfs()

        predictions_df = gql_dfs["pdr_predictions"]

        assert (
            predictions_df is not None and len(predictions_df) > 0
        ), "Lake has no predictions."

        self.predictions_df = predictions_df

    def filter_timestamp(self, start_timestr, end_timestr):
        predictions_df = self.predictions_df

        predictions_df = predictions_df.filter(
            (predictions_df["timestamp"] >= timestr_to_ut(start_timestr))
            & (predictions_df["timestamp"] <= timestr_to_ut(end_timestr))
        )

        self.predictions_df = predictions_df

    def filter_feed_addrs(self, feed_addrs):
        if len(feed_addrs) <= 0:
            return
        feed_addrs = [f.lower() for f in feed_addrs]

        predictions_df = self.predictions_df
        predictions_df = predictions_df.filter(
            predictions_df["ID"]
            .map_elements(lambda x: x.split("-")[0].lower())
            .is_in(feed_addrs)
        )
        self.predictions_df = predictions_df

    def filter_user_addrs(self, pdr_addrs):
        if len(pdr_addrs) <= 0:
            return

        pdr_addrs = [f.lower() for f in pdr_addrs]

        predictions_df = self.predictions_df
        predictions_df = predictions_df.filter(predictions_df["user"].is_in(pdr_addrs))
        self.predictions_df = predictions_df


@enforce_types
def get_predictions_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, feed_addrs: List[str]
):
    gql_data_factory = GQLDataFactory(ppss)
    gql_tables = gql_data_factory.get_gql_tables()

    predictions_df = gql_tables["pdr_predictions"].df
    assert (
        predictions_df is not None and len(predictions_df) > 0
    ), "Lake has no predictions."

    # filter by feed addresses
    if len(feed_addrs) > 0:
        feed_addrs = [f.lower() for f in feed_addrs]
        predictions_df = predictions_df.filter(
            predictions_df["ID"]
            .map_elements(lambda x: x.split("-")[0].lower())
            .is_in(feed_addrs)
        )

    # filter by start and end dates
    predictions_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(start_timestr))
        & (predictions_df["timestamp"] <= timestr_to_ut(end_timestr))
    )

    assert len(predictions_df) > 0, "No records to summarize. Please adjust params."

    feed_summary_df = get_feed_summary_stats(predictions_df)
    logger.info(feed_summary_df)


@enforce_types
def get_predictoors_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, pdr_addrs: List[str]
):
    pred_filter = PredFilter(ppss)
    pred_filter.filter_user_addrs(pdr_addrs)
    pred_filter.filter_timestamp(start_timestr, end_timestr)
    predictions_df = pred_filter.predictions_df

    assert len(predictions_df) > 0, "No records to summarize. Please adjust params."

    predictoor_summary_df = get_predictoor_summary_stats(predictions_df)
    logger.info(predictoor_summary_df)


@enforce_types
def get_traction_info_main(ppss: PPSS, start_timestr: str, end_timestr: str):
    pred_filter = PredFilter(ppss)
    pred_filter.filter_timestamp(start_timestr, end_timestr)
    predictions_df = pred_filter.predictions_df

    assert len(predictions_df) > 0, "No records to summarize. Please adjust params."

    # calculate predictoor traction statistics and draw plots
    stats_df = get_traction_statistics(predictions_df)
    plot_traction_cum_sum_statistics(stats_df, ppss.lake_ss.parquet_dir)
    plot_traction_daily_statistics(stats_df, ppss.lake_ss.parquet_dir)

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions_df)
    plot_slot_daily_statistics(slots_df, ppss.lake_ss.parquet_dir)
