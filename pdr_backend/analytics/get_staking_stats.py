"""This module currently gives traction wrt predictoors.
At some point, we can expand it into traction info wrt traders & txs too.
"""
from enforce_typing import enforce_types
from datetime import datetime
import polars as pl

from pdr_backend.analytics.predictoor_stats import (
    get_slot_statistics,
    get_mean_slots_df
)
from pdr_backend.lake.gql_data_factory import GQLDataFactory
from pdr_backend.ppss.ppss import PPSS


@enforce_types
def view_staking_statistics(slots_df):
    # calculate stats for the last 1, 3, 5, 10, 25 slots
    # columns = ["1", "3", "5", "10", "25"]
    # 1 row per pair_timeframe
    staking_daily_stats_df = (
        slots_df.group_by(["pair_timeframe", "slot"])
        .map_groups(
            lambda df: get_mean_slots_df(df.sample(5))
            if len(df) > 5
            else get_mean_slots_df(df)
        )
        .group_by("datetime")
        .agg(
            [
                pl.col("mean_stake").last().alias("daily_average_stake"),
                pl.col("mean_payout").sum().alias("daily_average_payout"),
                pl.col("mean_n_predictoors")
                .mean()
                .alias("daily_average_predictoor_count"),
            ]
        )
        .sort("datetime")
    )

    print("Staking statistics:")
    print(slots_df)


@enforce_types
def get_staking_stats_main(
    ppss: PPSS, pq_dir: str
):
    # start_timestr = 48 hours ago
    # end_timestr = now
    start_timestr = (datetime.datetime.now() - datetime.timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_timestr = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    data_ss = ppss.data_ss
    data_ss.d["st_timestr"] = start_timestr
    data_ss.d["fin_timestr"] = end_timestr

    gql_data_factory = GQLDataFactory(ppss)
    gql_dfs = gql_data_factory.get_gql_dfs()

    if len(gql_dfs) == 0:
        print("No records found. Please adjust start and end times.")
        return

    predictions_df = gql_dfs["pdr_predictions"]

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions_df)
    view_staking_statistics(slots_df)
