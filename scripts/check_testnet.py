import sys
import time
from pdr_backend.models.base_config import BaseConfig
from pdr_backend.models.token import Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.subgraph import query_subgraph


def print_stats(contract, field_name, threshold=0.9):
    count = sum(1 for _ in contract["slots"])
    with_field = sum(1 for slot in contract["slots"] if len(slot[field_name]) > 0)

    status = "OK" if with_field / count > threshold else "FAIL"
    token_name = contract["token"]["name"]

    print(f"{token_name}: {with_field}/{count} - {status}")


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
        header = f"{'-' * 10} {name}'s Wallet {'-' * 10}"
        address_line = f"Address: {value}"
        ocean_line = f"OCEAN Balance: {ocean_bal:.2f}"
        native_line = f"Native Balance: {native_bal:.2f}"

        ocean_warning = "WARNING: Low OCEAN balance!" if ocean_bal < 10 else ""
        native_warning = "WARNING: Low Native balance!" if native_bal < 10 else ""

        print(header)
        print(address_line)
        print(ocean_line)
        if ocean_warning:
            print(ocean_warning)
        print(native_line)
        if native_warning:
            print(native_warning)
        print("-" * len(header))
        print()
