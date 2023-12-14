"""This module currently gives traction wrt predictoors.
At some point, we can expand it into traction info wrt traders & txs too.
"""

from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.predictoor_stats import (
    get_traction_statistics,
    get_slot_statistics,
    plot_traction_cum_sum_statistics,
    plot_traction_daily_statistics,
    plot_slot_daily_statistics,
)
from pdr_backend.data_eng.gql_data_factory import GQLDataFactory


@enforce_types
def get_traction_info_main(
    ppss: PPSS, start_timestr: str, end_timestr: str, pq_dir: str
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

    # calculate predictoor traction statistics and draw plots
    stats_df = get_traction_statistics(predictions_df)
    plot_traction_cum_sum_statistics(stats_df, pq_dir)
    plot_traction_daily_statistics(stats_df, pq_dir)

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions_df)
    plot_slot_daily_statistics(slots_df, pq_dir)
