import math
import sys
import time
from addresses import get_opf_addresses
from pdr_backend.models.base_config import BaseConfig
from pdr_backend.models.token import Token
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
    if count == 0:
        count += 1
    status = "PASS" if with_field / count > threshold else "FAIL"
    token_name = contract_dict["token"]["name"]
    timeframe = seconds_to_text(int(contract_dict["secondsPerEpoch"]))
    print(f"{token_name} {timeframe}: {with_field}/{count} {field_name} - {status}")


def check_dfbuyer(dfbuyer_addr, contract_query_result, subgraph_url, tokens):
    ts_now = time.time()
    ts_start_time = int((ts_now // WEEK) * WEEK)
    contract_addresses = [
        i["id"] for i in contract_query_result["data"]["predictContracts"]
    ]
    sofar = get_consume_so_far_per_contract(
        subgraph_url,
        dfbuyer_addr,
        ts_start_time,
        contract_addresses,
    )
    expected = get_expected_consume(int(ts_now), tokens)
    print(
        f"Checking consume amounts (dfbuyer), expecting {expected} consume per contract"
    )
    for addr in contract_addresses:
        x = sofar[addr]
        log_text = "PASS" if x >= expected else "FAIL"
        print(
            f"    {log_text}... got {x} consume for contract: {addr}, expected {expected}"
        )


def get_expected_consume(for_ts: int, tokens: int):
    amount_per_feed_per_interval = tokens / 7 / 20
    week_start = (math.floor(for_ts / WEEK)) * WEEK
    time_passed = for_ts - week_start
    n_intervals = int(time_passed / 86400) + 1
    return n_intervals * amount_per_feed_per_interval


if __name__ == "__main__":
    config = BaseConfig()

    lookback_hours = 24
    if len(sys.argv) > 1:
        try:
            lookback_hours = int(sys.argv[1])
        except ValueError:
            print("Please provide a valid integer as the number of epochs to check!")

    addresses = get_opf_addresses(config.web3_config.w3.eth.chain_id)

    ts = int(time.time())
    ts_start = ts - lookback_hours * 60 * 60
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
                    slots(where:{slot_lt:%s, slot_gt:%s} orderBy: slot orderDirection:desc first:1000){
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
        ts_start,
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
    # pylint: disable=line-too-long
    ocean_address = (
        "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520"
        if config.web3_config.w3.eth.chain_id == 23294
        else "0x973e69303259B0c2543a38665122b773D28405fB"
    )
    ocean_token = Token(config.web3_config, ocean_address)

    for name, value in addresses.items():
        ocean_bal_wei = ocean_token.balanceOf(value)
        native_bal_wei = config.web3_config.w3.eth.get_balance(value)

        ocean_bal = ocean_bal_wei / 1e18
        native_bal = native_bal_wei / 1e18

        ocean_warning = " WARNING LOW OCEAN BALANCE!" if ocean_bal < 10 else " OK "
        native_warning = " WARNING LOW NATIVE BALANCE!" if native_bal < 10 else " OK "

        if name == "trueval":
            ocean_warning = " OK "

        # pylint: disable=line-too-long
        print(
            f"{name}: OCEAN: {ocean_bal:.2f}{ocean_warning}, Native: {native_bal:.2f}{native_warning}"
        )

    # ---------------- dfbuyer ----------------

    token_amt = 37000
    check_dfbuyer(addresses["dfbuyer"].lower(), result, config.subgraph_url, token_amt)
