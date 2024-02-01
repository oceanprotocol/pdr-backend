import math
from typing import Union

from enforce_typing import enforce_types

from pdr_backend.cli.timeframe import s_to_timeframe_str
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.subgraph_consume_so_far import get_consume_so_far_per_contract
from pdr_backend.util.constants import S_PER_DAY, S_PER_WEEK
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.util.mathutil import from_wei
from pdr_backend.util.timeutil import current_ut_s

_N_FEEDS = 20  # magic number alert. FIX ME, shouldn't be hardcoded


@enforce_types
def print_stats(contract_dict: dict, field_name: str, threshold: float = 0.9):
    n_slots = len(contract_dict["slots"])
    n_slots_with_field = sum(
        1 for slot in contract_dict["slots"] if len(slot[field_name]) > 0
    )
    if n_slots == 0:
        n_slots = 1

    status = "PASS" if n_slots_with_field / n_slots > threshold else "FAIL"
    token_name = contract_dict["token"]["name"]

    s_per_epoch = int(contract_dict["secondsPerEpoch"])
    timeframe_str = s_to_timeframe_str(s_per_epoch)
    print(
        f"{token_name} {timeframe_str}: "
        f"{n_slots_with_field}/{n_slots} {field_name} - {status}"
    )


@enforce_types
def check_dfbuyer(
    dfbuyer_addr: str,
    contract_query_result: dict,
    subgraph_url: str,
    token_amt: int,
):
    cur_ut = current_ut_s()
    start_ut = int((cur_ut // S_PER_WEEK) * S_PER_WEEK)

    contracts_sg_dict = contract_query_result["data"]["predictContracts"]
    contract_addresses = [
        contract_sg_dict["id"] for contract_sg_dict in contracts_sg_dict
    ]
    amt_consume_so_far = get_consume_so_far_per_contract(
        subgraph_url,
        dfbuyer_addr,
        start_ut,
        contract_addresses,
    )
    expect_amt_consume = get_expected_consume(cur_ut, token_amt)
    print(
        "Checking consume amounts (dfbuyer)"
        f", expecting {expect_amt_consume} consume per contract"
    )
    for addr in contract_addresses:
        x = amt_consume_so_far[addr]
        log_text = "PASS" if x >= expect_amt_consume else "FAIL"
        print(
            f"    {log_text}... got {x} consume for contract: {addr}"
            f", expected {expect_amt_consume}"
        )


@enforce_types
def get_expected_consume(for_ut: int, token_amt: int) -> Union[float, int]:
    """
    @arguments
      for_ut -- unix time, in ms, in UTC time zone
      token_amt -- # tokens

    @return
      exp_consume --
    """
    amt_per_feed_per_week = token_amt / 7 / _N_FEEDS
    week_start_ut = (math.floor(for_ut / S_PER_WEEK)) * S_PER_WEEK
    time_passed = for_ut - week_start_ut
    n_weeks = int(time_passed / S_PER_DAY) + 1
    return n_weeks * amt_per_feed_per_week


@enforce_types
def do_query_network(subgraph_url: str, lookback_hours: int):
    cur_ut = current_ut_s()
    start_ut = cur_ut - lookback_hours * 60 * 60
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
        cur_ut,
        start_ut,
    )
    return query_subgraph(subgraph_url, query, timeout=10.0)


@enforce_types
def check_network_main(ppss: PPSS, lookback_hours: int):
    web3_pp = ppss.web3_pp
    result = do_query_network(web3_pp.subgraph_url, lookback_hours)

    # check no of contracts
    no_of_contracts = len(result["data"]["predictContracts"])
    status = "OK" if no_of_contracts >= 11 else "FAILED"

    print(f"Number of Predictoor contracts: {no_of_contracts} - {status}")
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

    OCEAN = web3_pp.OCEAN_Token

    addresses = get_opf_addresses(web3_pp.network)
    for name, address in addresses.items():
        ocean_bal = from_wei(OCEAN.balanceOf(address))
        # TODO: wrap in web3 pp?
        native_bal = from_wei(web3_pp.web3_config.w3.eth.get_balance(address))

        ocean_warning = (
            " WARNING LOW OCEAN BALANCE!"
            if ocean_bal < 10 and name != "trueval"
            else " OK "
        )
        native_warning = " WARNING LOW NATIVE BALANCE!" if native_bal < 10 else " OK "

        print(
            f"{name}: OCEAN: {ocean_bal:.2f}{ocean_warning}"
            f", Native: {native_bal:.2f}{native_warning}"
        )

    # ---------------- dfbuyer ----------------

    dfbuyer_addr = addresses["dfbuyer"].lower()
    token_amt = 44460
    check_dfbuyer(dfbuyer_addr, result, web3_pp.subgraph_url, token_amt)
