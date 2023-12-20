from typing import Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.csvs import save_analysis_csv
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.analytics.predictoor_stats import get_predictoor_summary_stats, get_feed_summary_stats
from pdr_backend.subgraph.subgraph_predictions import (
    get_all_contract_ids_by_owner,
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut
from pdr_backend.lake.gql_data_factory import GQLDataFactory


@enforce_types
def get_predictions_info_main(
    ppss: PPSS,
    feed_addrs_str: Union[str, None],
    start_timestr: str,
    end_timestr: str,
    pq_dir: str,
):
    data_ss = ppss.data_ss
    data_ss.d["st_timestr"] = start_timestr
    data_ss.d["fin_timestr"] = end_timestr

    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    if len(gql_dfs) == 0:
        print("No records found. Please adjust start and end times.")
        return

    predictions_df = gql_dfs["pdr_predictions"]

    predictoor_summary_df = get_predictoor_summary_stats(predictions_df)
    #feed_summary_df = get_feed_summary_stats(predictions_df)
