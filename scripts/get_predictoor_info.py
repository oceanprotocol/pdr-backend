import sys
from pdr_backend.util.csvs import write_csv
from pdr_backend.util.predictoor_stats import get_cli_statistics
from pdr_backend.util.subgraph_predictions import get_all_predictions
from pdr_backend.accuracy.utils.filter_mode import FilterMode
from pdr_backend.predictoor.approach3.timeutil import timestr_to_ut

if __name__ == "__main__":
    if len(sys.argv) != 6:
        # pylint: disable=line-too-long
        print(
            "Usage: python get_predictoor_info.py [predictoor_addr | str] [start_date | yyyy-mm-dd] [end_date | yyyy-mm-dd] [network | mainnet | testnet] [csv_output_dir | str]"
        )
        sys.exit(1)

    # single address or multiple addresses separated my comma
    predictoor_addrs = sys.argv[1]

    # yyyy-mm-dd
    start_dt = sys.argv[2]
    end_dt = sys.argv[3]

    # mainnet or tesnet
    network_param = sys.argv[4]

    csv_output_dir_param = sys.argv[5]

    start_ts_param = timestr_to_ut(start_dt)
    end_ts_param = timestr_to_ut(end_dt)

    if "," in predictoor_addrs:
        address_filter = predictoor_addrs.lower().split(",")
    else:
        address_filter = [predictoor_addrs.lower()]

    _predictions = get_all_predictions(
        start_ts_param,
        end_ts_param,
        address_filter,
        network_param,
        FilterMode.PREDICTOOR,
    )

    write_csv(_predictions, csv_output_dir_param)

    get_cli_statistics(_predictions)
