from typing import Union

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.csvs import save_analysis_csv
from pdr_backend.util.predictoor_stats import get_cli_statistics
from pdr_backend.util.subgraph_predictions import (
    get_all_contract_ids_by_owner,
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_predictions_info_main(
    ppss: PPSS,
    feed_addrs_str: Union[str, None],
    start_timestr: str,
    end_timestr: str,
    pq_dir: str,
):
    # get network
    # TO DO: This code has DRY problems. Reduce.
    if "main" in ppss.web3_pp.network:
        network = "mainnet"
    elif "test" in ppss.web3_pp.network:
        network = "testnet"
    else:
        raise ValueError(ppss.web3_pp.network)

    start_ut: int = ms_to_seconds(timestr_to_ut(start_timestr))
    end_ut: int = ms_to_seconds(timestr_to_ut(end_timestr))

    # filter by feed contract address
    feed_contract_list = get_all_contract_ids_by_owner(
        owner_address=ppss.web3_pp.owner_addrs,
        network=network,
    )
    feed_contract_list = [f.lower() for f in feed_contract_list]

    if feed_addrs_str:
        keep = feed_addrs_str.lower().split(",")
        feed_contract_list = [f for f in feed_contract_list if f in keep]

    # fetch predictions
    predictions = fetch_filtered_predictions(
        start_ut,
        end_ut,
        feed_contract_list,
        network,
        FilterMode.CONTRACT,
        payout_only=True,
        trueval_only=True,
    )

    if not predictions:
        print("No records found. Please adjust start and end times.")
        return

    save_analysis_csv(predictions, pq_dir)

    get_cli_statistics(predictions)
