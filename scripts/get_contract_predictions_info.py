import sys
from pdr_backend.util.csvs import write_analysis_prediction
from pdr_backend.util.predictoor_stats import get_cli_statistics
from pdr_backend.util.subgraph_predictions import fetch_filtered_predictions, FilterMode
from pdr_backend.util.timeutil import ms_to_seconds, timestr_to_ut
from pdr_backend.util.subgraph_predictions import get_all_contract_ids_by_owner

if __name__ == "__main__":
    if len(sys.argv) != 6:
        # pylint: disable=line-too-long
        print(
            "Usage: python get_contract_predictions_info.py [contract_addr | 'all'] [start_date | yyyy-mm-dd] [end_date | yyyy-mm-dd] [network | mainnet | testnet] [csv_output_dir | str]"
        )
        sys.exit(1)

    # single address or multiple addresses separated my comma
    contract_addr = sys.argv[1]

    # yyyy-mm-dd
    start_dt = sys.argv[2]
    end_dt = sys.argv[3]

    # mainnet or tesnet
    network_param = sys.argv[4]

    csv_output_dir_param = sys.argv[5]

    start_ts_param = ms_to_seconds(timestr_to_ut(start_dt))
    end_ts_param = ms_to_seconds(timestr_to_ut(end_dt))

    if "," in contract_addr:
        address_filter = contract_addr.lower().split(",")
    elif contract_addr == "all":
        addresses = get_all_contract_ids_by_owner(
            owner_address="0x4ac2e51f9b1b0ca9e000dfe6032b24639b172703",
            network="mainnet",
        )
        address_filter = [address.lower() for address in addresses]
    else:
        address_filter = [contract_addr.lower()]

    _predictions = fetch_filtered_predictions(
        start_ts_param,
        end_ts_param,
        address_filter,
        network_param,
        FilterMode.CONTRACT,
    )

    write_analysis_prediction(_predictions, csv_output_dir_param)

    get_cli_statistics(_predictions)
