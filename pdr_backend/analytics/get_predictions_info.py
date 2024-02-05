from typing import List

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.analytics.predictoor_stats import get_feed_summary_stats
from pdr_backend.util.timeutil import timestr_to_ut


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
    print(feed_summary_df)
