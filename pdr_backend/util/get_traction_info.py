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
from pdr_backend.util.subgraph_predictions import (
    get_all_contract_ids_by_owner,
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_traction_info_main(
    ppss: PPSS, addrs_str: str, start_timestr: str, end_timestr: str, pq_dir: str
):
    # get network
    if "main" in ppss.web3_pp.network:
        network = "mainnet"
    elif "test" in ppss.web3_pp.network:
        network = "testnet"
    else:
        raise ValueError(ppss.web3_pp.network)

    start_ut: int = ms_to_seconds(timestr_to_ut(start_timestr))
    end_ut: int = ms_to_seconds(timestr_to_ut(end_timestr))

    # filter by contract address
    if addrs_str == "":
        address_filter = []
    elif "," in addrs_str:
        address_filter = addrs_str.lower().split(",")
    else:
        address_filter = [addrs_str.lower()]

    contract_list = get_all_contract_ids_by_owner(
        owner_address=ppss.web3_pp.owner_addrs,
        network=network,
    )

    contract_list = [
        x.lower()
        for x in contract_list
        if x.lower() in address_filter or address_filter == []
    ]

    # fetch predictions
    predictions = fetch_filtered_predictions(
        start_ut,
        end_ut,
        contract_list,
        network,
        FilterMode.CONTRACT,
        payout_only=False,
        trueval_only=False,
    )

    if len(predictions) == 0:
        print("No records found. Please adjust start and end times.")
        return

    # calculate predictoor traction statistics and draw plots
    stats_df = get_traction_statistics(predictions)
    plot_traction_cum_sum_statistics(stats_df, pq_dir)
    plot_traction_daily_statistics(stats_df, pq_dir)

    # calculate slot statistics and draw plots
    slots_df = get_slot_statistics(predictions)
    plot_slot_daily_statistics(slots_df, pq_dir)
