from enforce_typing import enforce_types
from typing import List

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.predictoor_stats import get_system_statistics
from pdr_backend.util.subgraph_predictions import (
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_system_info_main(
    ppss: PPSS,
    contract_addrs: List[str],
    start_timestr: str,
    end_timestr: str
):
    if "main" in ppss.web3_pp.network:
        network = "mainnet"
    elif "test" in ppss.web3_pp.network:
        network = "testnet"
    else:
        raise ValueError(ppss.web3_pp.network)

    start_ut: int = ms_to_seconds(timestr_to_ut(start_timestr))
    end_ut: int = ms_to_seconds(timestr_to_ut(end_timestr))

    predictions = fetch_filtered_predictions(
        start_ut,
        end_ut,
        contract_addrs,
        network,
        FilterMode.CONTRACT,
        payout_only=False,
        trueval_only=False
    )

    stats_df = get_system_statistics(predictions)
    print("stats_df", stats_df)