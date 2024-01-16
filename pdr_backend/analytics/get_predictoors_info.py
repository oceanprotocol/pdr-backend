from typing import Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.analytics.predictoor_stats import get_predictoor_summary_stats
from pdr_backend.lake.gql_data_factory import GQLDataFactory
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

    # filter by user addresses
    if pdr_addrs_str:
        pdr_addrs_list = pdr_addrs_str.lower().split(",")
        predictions_df = predictions_df.filter(
            predictions_df["user"].is_in(pdr_addrs_list)
        )

    # filter by start and end dates
    predictions_df = predictions_df.filter(
        (predictions_df["timestamp"] >= timestr_to_ut(start_timestr) / 1000)
        & (predictions_df["timestamp"] <= timestr_to_ut(end_timestr) / 1000)
    )

    predictoor_summary_df = get_predictoor_summary_stats(predictions_df)
    print(predictoor_summary_df)
