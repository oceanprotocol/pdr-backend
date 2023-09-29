import math
import sys
import time
from pdr_backend.models.base_config import BaseConfig
from pdr_backend.models.token import Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.subgraph import get_consume_so_far_per_contract, query_subgraph

WEEK = 86400 * 7


def seconds_to_text(seconds: int) -> str:
    if seconds == 300:
        return "5m"
    if seconds == 3600:
        return "1h"
    return ""


def print_stats(contract_dict, field_name, threshold=0.9):
    count = sum(1 for _ in contract_dict["slots"])
    with_field = sum(1 for slot in contract_dict["slots"] if len(slot[field_name]) > 0)

    status = "PASS" if with_field / count > threshold else "FAIL"
    token_name = contract_dict["token"]["name"]
    timeframe = seconds_to_text(int(contract_dict["secondsPerEpoch"]))
    print(f"{token_name} {timeframe}: {with_field}/{count} {field_name} - {status}")


def check_dfbuyer(dfbuyer_addr, contract_query_result):
    ts_now = time.time()
    ts_start_time = int((ts_now // WEEK) * WEEK)
    sofar = get_consume_so_far_per_contract(
        config.subgraph_url,
        dfbuyer_addr,
        ts_start_time,
        [i["id"] for i in contract_query_result["data"]["predictContracts"]],
    )
    expected = get_expected_consume(int(ts_now))
    print(
        f"Checking consume amounts (dfbuyer), expecting {expected} consume per contract"
    )
    for addr, x in sofar.items():
        log_text = "PASS" if x >= expected else "FAIL"
        print(
            f"    {log_text}... got {x} consume for contract: {addr}, expected {expected}"
        )


def get_expected_consume(for_ts: int):
    amount_per_feed_per_interval = 37000 / 7 / 20
    week_start = (math.floor(for_ts / WEEK)) * WEEK
    time_passed = for_ts - week_start
    n_intervals = int(time_passed / 86400) + 1
    return n_intervals * amount_per_feed_per_interval


if __name__ == "__main__":
    config = BaseConfig()

    no_of_epochs_to_check = 288
    if len(sys.argv) > 1:
        try:
            no_of_epochs_to_check = int(sys.argv[1])
        except ValueError:
            print("Please provide a valid integer as the number of epochs to check!")

    addresses = {
        "predictoor1": "0xE02A421dFc549336d47eFEE85699Bd0A3Da7D6FF",
        "predictoor2": "0x00C4C993e7B0976d63E7c92D874346C3D0A05C1e",
        "predictoor3": "0x005C414442a892077BD2c1d62B1dE2Fc127E5b9B",
        "trueval": "0x005FD44e007866508f62b04ce9f43dd1d36D0c0c",
        "websocket": "0x008d4866C4071AC9d74D6359604762C7B581D390",
        "dfbuyer": "0xeA24C440eC55917fFa030C324535fc49B42c2fD7",
    }

    ts = int(time.time())
    query = """
            {
                predictContracts{
                    id
                    token{
                        name
                    }
                    subscriptions(orderBy: expireTime orderDirection:desc first:10){
                        user {
                            id
                        }
                        expireTime
                    }
                    slots(where:{slot_lt:%s} orderBy: slot orderDirection:desc first:%s){
                        slot
                        roundSumStakesUp
                        roundSumStakes
                        predictions(orderBy: timestamp orderDirection:desc){
                            stake
                            user {
                                id
                            }
                            timestamp
                            payout{
                                payout
                                predictedValue
                                trueValue
                            }
                        }
                        trueValues{
                            trueValue
                        }
                    }
                    secondsPerEpoch
                } 
            }
            """ % (
        ts,
        no_of_epochs_to_check,
    )
    result = query_subgraph(config.subgraph_url, query, timeout=10.0)
    # check no of contracts
    no_of_contracts = len(result["data"]["predictContracts"])
    if no_of_contracts >= 11:
        print(f"Number of Predictoor contracts: {no_of_contracts} - OK")
    else:
        print(f"Number of Predictoor contracts: {no_of_contracts} - FAILED")

    print("-" * 60)
    # check number of predictions
    print("Predictions:")
    for contract in result["data"]["predictContracts"]:
        print_stats(contract, "predictions")

    print()

    # Check number of truevals
    print("True Values:")
    for contract in result["data"]["predictContracts"]:
        print_stats(contract, "trueValues")
    print("\nChecking account balances")
    ocean_address = get_address(config.web3_config.w3.eth.chain_id, "Ocean")
    ocean_token = Token(config.web3_config, ocean_address)

    for name, value in addresses.items():
        ocean_bal_wei = ocean_token.balanceOf(value)
        native_bal_wei = config.web3_config.w3.eth.get_balance(value)

        ocean_bal = ocean_bal_wei / 1e18
        native_bal = native_bal_wei / 1e18

        ocean_warning = " WARNING LOW OCEAN BALANCE!" if ocean_bal < 100 else " OK "
        native_warning = " WARNING LOW NATIVE BALANCE!" if native_bal < 50 else " OK "

        print(
            f"{name}: OCEAN: {ocean_bal:.2f}{ocean_warning}, Native: {native_bal:.2f}{native_warning}"
        )

    # ---------------- dfbuyer ----------------

    check_dfbuyer(addresses["dfbuyer"].lower(), result)
