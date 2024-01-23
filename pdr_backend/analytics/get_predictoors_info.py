from typing import Union

from enforce_typing import enforce_types
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.analytics.predictoor_stats import get_predictoor_summary_stats
from pdr_backend.ppss.ppss import PPSS


@enforce_types
def get_predictoors_info_main(ppss: PPSS, pdr_addrs_str: Union[str, None]):
    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    predictions_df = gql_dfs["pdr_predictions"]
    assert (
        predictions_df is not None and len(predictions_df) > 0
    ), "Lake has no predictions."

    # filter by user addresses
    if pdr_addrs_str:
        pdr_addrs_list = pdr_addrs_str.lower().split(",")
        predictions_df = predictions_df.filter(
            predictions_df["user"].is_in(pdr_addrs_list)
        )

    # filter by start and end dates
    predictions_df = predictions_df.filter(
        (predictions_df["timestamp"] >= ppss.lake_ss.st_timestamp / 1000)
        & (predictions_df["timestamp"] <= ppss.lake_ss.fin_timestamp / 1000)
    )

    assert len(predictions_df) > 0, "No records to summarize. Please adjust params."

    predictoor_summary_df = get_predictoor_summary_stats(predictions_df)
    print(predictoor_summary_df)
