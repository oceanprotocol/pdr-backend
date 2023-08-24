from datetime import datetime, timedelta, timezone
from os import getenv
import os
import threading
import time
from typing import Dict

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.subgraph import query_predictContractss
from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.util.web3_config import Web3Config
from pdr_backend.trueval.subgraph import get_pending_slots
from pdr_backend.util.contract import PredictoorContract, Web3Config
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.models import Slot


rpc_url = getenv_or_exit("RPC_URL")
subgraph_url = getenv_or_exit("SUBGRAPH_URL")
private_key = getenv_or_exit("PRIVATE_KEY")
pair_filters = getenv("PAIR_FILTER")
timeframe_filter = getenv("TIMEFRAME_FILTER")
source_filter = getenv("SOURCE_FILTER")
owner_addresses = getenv("OWNER_ADDRS")

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner

""" Get all intresting topics that we can submit trueval """
topics: Dict[str, dict] = {}
contract_cache: Dict[str, tuple] = {}


class NewTrueVal:
    def __init__(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
        seconds_per_epoch,
    ):
        self.slot = slot
        self.predictoor_contract = predictoor_contract
        self.current_ts = slot.slot
        self.seconds_per_epoch = seconds_per_epoch

    def run(self) -> dict:
        """
        Get timestamp of previous epoch-2 , get the price
        Get timestamp of previous epoch-1, get the price
        Compare and submit trueval
        """
        self.slot.slot = int(self.slot.slot)
        initial_ts = self.slot.slot - self.seconds_per_epoch
        end_ts = self.slot.slot

        (true_val, cancel_round) = get_true_val(self.slot.contract, initial_ts, end_ts)
        print(
            f"Contract:{self.predictoor_contract.contract_address} - Submitting true_val {true_val} and slot:{self.slot.slot}"
        )

        tx = self.predictoor_contract.submit_trueval(
            true_val, self.slot.slot, cancel_round, True
        )

        return tx


def process_slot(slot: Slot) -> dict:
    contract_address = slot.contract.address
    if contract_address in contract_cache:
        predictoor_contract, seconds_per_epoch = contract_cache[contract_address]
    else:
        predictoor_contract = PredictoorContract(web3_config, contract_address)
        seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
        contract_cache[contract_address] = (
            predictoor_contract,
            seconds_per_epoch,
        )
    trueval = NewTrueVal(slot, predictoor_contract, seconds_per_epoch)
    return trueval.run()


def main():
    while True:
        sleep_time = os.getenv("SLEEP_TIME", 30)
        batch_size = os.getenv("BATCH_SIZE", 50)

        pending_contracts = get_pending_slots(subgraph_url, web3_config)
        print(f"Found {len(pending_contracts)} pending slots, processing {batch_size}")
        pending_contracts = pending_contracts[:batch_size]

        results = []

        if len(pending_contracts) > 0:
            # try:
            for slot in pending_contracts:
                print(
                    f"Processing slot {slot.slot} for contract {slot.contract.address}"
                )
                tx = process_slot(
                    slot,
                )
                results.append(tx)
        print(f"Sleeping for {sleep_time} seconds...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
