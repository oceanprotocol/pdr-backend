from enforce_typing import enforce_types
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.predictoor_stats import (
    get_predictoor_traction_statistics,
    plot_predictoor_traction_cum_sum_statistics,
    plot_predictoor_traction_daily_statistics,
)
from pdr_backend.util.subgraph_predictions import (
    get_all_contract_ids_by_owner,
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_predictoor_traction_info_main(
    ppss: PPSS, addrs_str: str, start_timestr: str, end_timestr: str, csvs_dir: str
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

    # calculate statistics and draw plots
    stats_df = get_predictoor_traction_statistics(predictions)

    plot_predictoor_traction_cum_sum_statistics(csvs_dir, stats_df)
    plot_predictoor_traction_daily_statistics(csvs_dir, stats_df)
