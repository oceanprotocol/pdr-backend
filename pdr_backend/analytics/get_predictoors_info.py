from typing import Union

from enforce_typing import enforce_types

from pdr_backend.analytics.predictoor_stats import get_cli_statistics
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_predictions import (
    FilterMode,
    fetch_filtered_predictions,
)
from pdr_backend.util.csvs import save_prediction_csv
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut


@enforce_types
def get_predictoors_info_main(
    ppss: PPSS,
    pdr_addrs_str: Union[str, None],
    start_timestr: str,
    end_timestr: str,
    csv_output_dir: str,
):
    network = get_sapphire_postfix(ppss.web3_pp.network)
    start_ut: int = ms_to_seconds(timestr_to_ut(start_timestr))
    end_ut: int = ms_to_seconds(timestr_to_ut(end_timestr))

    pdr_addrs_filter = []
    if pdr_addrs_str:
        pdr_addrs_filter = pdr_addrs_str.lower().split(",")

    predictions = fetch_filtered_predictions(
        start_ut,
        end_ut,
        pdr_addrs_filter,
        network,
        FilterMode.PREDICTOOR,
    )

    save_prediction_csv(predictions, csv_output_dir)

    get_cli_statistics(predictions)
