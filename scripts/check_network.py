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
    if count == 0:
        count += 1
    status = "PASS" if with_field / count > threshold else "FAIL"
    token_name = contract_dict["token"]["name"]
    timeframe = seconds_to_text(int(contract_dict["secondsPerEpoch"]))
    print(f"{token_name} {timeframe}: {with_field}/{count} {field_name} - {status}")


def check_dfbuyer(dfbuyer_addr, contract_query_result, subgraph_url):
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
    expected = get_expected_consume(int(ts_now))
    print(
        f"Checking consume amounts (dfbuyer), expecting {expected} consume per contract"
    )
    for addr in contract_addresses:
        x = sofar[addr]
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

    addresses = {}

    if config.web3_config.w3.eth.chain_id == 23295:
        addresses = {
            "predictoor1": "0xE02A421dFc549336d47eFEE85699Bd0A3Da7D6FF",
            "predictoor2": "0x00C4C993e7B0976d63E7c92D874346C3D0A05C1e",
            "predictoor3": "0x005C414442a892077BD2c1d62B1dE2Fc127E5b9B",
            "trueval": "0x005FD44e007866508f62b04ce9f43dd1d36D0c0c",
            "websocket": "0x008d4866C4071AC9d74D6359604762C7B581D390",
            "dfbuyer": "0xeA24C440eC55917fFa030C324535fc49B42c2fD7",
        }

    if config.web3_config.w3.eth.chain_id == 23294:
        addresses = {
            "predictoor1": "0x35Afee1168D1e1053298F368488F4eE95E891a6e",
            "predictoor2": "0x1628BeA0Fb859D56Cd2388054c0bA395827e4374",
            "predictoor3": "0x3f0825d0c0bbfbb86cd13C7E6c9dC778E3Bb44ec",
            "predictoor4": "0x20704E4297B1b014d9dB3972cc63d185C6C00615",
            "predictoor5": "0xf38426BF6c117e7C5A6e484Ed0C8b86d4Ae7Ff78",
            "predictoor6": "0xFe4A9C5F3A4EA5B1BfC089713ed5fce4bB276683",
            "predictoor7": "0x078F083525Ad1C0d75Bc7e329EE6656bb7C81b12",
            "predictoor8": "0x4A15CC5C20c5C5F71A9EA6376356f72b2A760f12",
            "predictoor9": "0xD2a24CB4ff2584bAD80FF5F109034a891c3d88dD",
            "predictoor10": "0x8a64CF23B5BB16Fd7444B47f94673B90Cc0F75cE",
            "predictoor11": "0xD15749B83Be987fEAFa1D310eCc642E0e24CadBA",
            "predictoor12": "0xAAbDBaB266b31d6C263b110bA9BE4930e63ce817",
            "predictoor13": "0xB6431778C00F44c179D8D53f0E3d13334C051bd3",
            "predictoor14": "0x2c2C599EC040F47C518fa96D08A92c5df5f50951",
            "predictoor15": "0x5C72F76F7dae16dD34Cb6183b73F4791aa4B3BC4",
            "predictoor16": "0x19C0A543664F819C7F9fb6475CE5b90Bfb112d26",
            "predictoor17": "0x8cC3E2649777d59809C8d3E2Dd6E90FDAbBed502",
            "predictoor18": "0xF5F2a495E0bcB50bF6821a857c5d4a694F5C19b4",
            "predictoor19": "0x4f17B06177D37E24158fec982D48563bCEF97Fe6",
            "predictoor20": "0x784b52987A894d74E37d494F91eD03a5Ab37aB36",
            "trueval": "0x886A892670A7afc719Dcf36eF92c798203F74B67",
            "websocket": "0x6Cc4Fe9Ba145AbBc43227b3D4860FA31AFD225CB",
            "dfbuyer": "0x2433e002Ed10B5D6a3d8d1e0C5D2083BE9E37f1D",
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

        ocean_warning = " WARNING LOW OCEAN BALANCE!" if ocean_bal < 10 else " OK "
        native_warning = " WARNING LOW NATIVE BALANCE!" if native_bal < 10 else " OK "

        # pylint: disable=line-too-long
        print(
            f"{name}: OCEAN: {ocean_bal:.2f}{ocean_warning}, Native: {native_bal:.2f}{native_warning}"
        )

    # ---------------- dfbuyer ----------------

    if config.web3_config.w3.eth.chain_id == 23295:
        # no data farming on mainnet yet
        check_dfbuyer(addresses["dfbuyer"].lower(), result, config.subgraph_url)
