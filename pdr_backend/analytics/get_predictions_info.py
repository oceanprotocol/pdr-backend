from typing import Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.analytics.predictoor_stats import get_feed_summary_stats
from pdr_backend.lake.gql_data_factory import GQLDataFactory


@enforce_types
def get_predictions_info_main(
    ppss: PPSS,
    feed_addrs_str: Union[str, None],
    start_timestr: str,
    end_timestr: str,
):
    lake_ss = ppss.lake_ss
    lake_ss.d["st_timestr"] = start_timestr
    lake_ss.d["fin_timestr"] = end_timestr

    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    if len(gql_dfs["pdr_predictions"]) == 0:
        print("No records found. Please adjust start and end times.")
        return
    predictions_df = gql_dfs["pdr_predictions"]

    if feed_addrs_str:
        feed_addrs_list = feed_addrs_str.lower().split(",")
        predictions_df = predictions_df.filter(
            predictions_df["ID"]
            .map_elements(lambda x: x.split("-")[0])
            .is_in(feed_addrs_list)
        )
    get_feed_summary_stats(predictions_df)
