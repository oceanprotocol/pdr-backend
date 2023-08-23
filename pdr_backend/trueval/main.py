from datetime import datetime, timedelta, timezone
from os import getenv
import os
import threading
import time
from typing import Dict

from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.trueval.subgraph import get_pending_slots
from pdr_backend.utils.contract import PredictoorContract, Web3Config
from pdr_backend.utils.env import getenv_or_exit
from pdr_backend.utils.models import Slot


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


class NewTrueVal(threading.Thread):
    def __init__(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
        nonce: int,
        seconds_per_epoch,
        index: int,
    ):
        super().__init__()
        self.slot = slot
        self.predictoor_contract = predictoor_contract
        self.current_ts = slot.slot

        self.nonce = nonce
        self.signature = None  # This will store the result
        self.seconds_per_epoch = seconds_per_epoch
        self.index = index

    def run(self):
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
            f"Contract:{self.predictoor_contract.contract_address} - Getting signature for true_val {true_val} and slot:{self.slot.slot}"
        )

        sig = self.predictoor_contract.trueval_sign(
            true_val, self.slot.slot, cancel_round, self.nonce, self.index
        )

        self.signature = {"signature": sig, "nonce": self.nonce}


def process_slot(slot: Slot, nonce: int, index: int) -> NewTrueVal:
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
    return NewTrueVal(slot, predictoor_contract, nonce, seconds_per_epoch, index)


def main():
    while True:
        sleep_time = os.getenv("SLEEP_TIME", 15)
        max_threads = os.getenv("MAX_THREADS", 50)

        pending_contracts = get_pending_slots(subgraph_url, web3_config)
        pending_contracts = pending_contracts[:max_threads]
        print(f"Found {len(pending_contracts)} pending slots")
        nonce = web3_config.w3.eth.get_transaction_count(owner)
        threads = []
        results = []

        if len(pending_contracts) > 0:
            # try:
            for slot in pending_contracts:
                sig = process_slot(
                    slot,
                    nonce,
                    len(pending_contracts) - pending_contracts.index(slot) + 1,
                )
                nonce += 1
                print(
                    f"Processing slot {slot.slot} for contract {slot.contract.address}"
                )
                # threading.Thread(target=sig.run, args=(thread_limiter,)).start()
                threads.append(sig)

            for thr in threads:
                thr.start()

            for thr in threads:
                thr.join()
                results.append(thr.signature)

            sorted_signatures = sorted(results, key=lambda x: x["nonce"])
            print(f"Generated {len(sorted_signatures)} signatures")

            print("Sending transactions...")
            for sig in sorted_signatures:
                while (
                    web3_config.w3.eth.get_transaction_count(owner, "pending")
                    != sig["nonce"]
                ):
                    time.sleep(2)
                tx = web3_config.w3.eth.send_raw_transaction(
                    sig["signature"].rawTransaction
                )
                # web3_config.w3.eth.wait_for_transaction_receipt(tx)
                print(f"Transaction {tx.hex()} sent")

        print("Sleeping for 15 seconds...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
