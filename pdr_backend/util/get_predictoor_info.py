from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.csvs import write_prediction_csv
from pdr_backend.util.predictoor_stats import get_cli_statistics
from pdr_backend.util.subgraph_predictions import (
    fetch_filtered_predictions,
    FilterMode,
)
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_predictoor_info_main(
    ppss: PPSS,
    predictoor_addrs: str,
    start_timestr: str,
    end_timestr: str,
    csv_output_dir: str,
):
    if "main" in ppss.web3_pp.network:
        network = "mainnet"
    elif "test" in ppss.web3_pp.network:
        network = "testnet"
    else:
        raise ValueError(ppss.web3_pp.network)

    start_ut: int = ms_to_seconds(timestr_to_ut(start_timestr))
    end_ut: int = ms_to_seconds(timestr_to_ut(end_timestr))

    if "," in predictoor_addrs:
        address_filter = predictoor_addrs.lower().split(",")
    else:
        address_filter = [predictoor_addrs.lower()]

    predictions = fetch_filtered_predictions(
        start_ut,
        end_ut,
        address_filter,
        network,
        FilterMode.PREDICTOOR,
    )

    write_prediction_csv(predictions, csv_output_dir)

    get_cli_statistics(predictions)
