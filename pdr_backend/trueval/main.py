import os
import time
import threading

from typing import Dict
from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.trueval.subgraph import get_pending_slots
from pdr_backend.utils.contract import PredictoorContract, Web3Config
from pdr_backend.utils import env
from pdr_backend.utils.models import Slot


rpc_url = env.get_rpc_url_or_exit()
subgraph_url = env.get_subgraph_or_exit()
private_key = env.get_private_key_or_exit()
pair_filters = env.get_pair_filter()
timeframe_filter = env.get_timeframe_filter()
source_filter = env.get_source_filter()
owner_addresses = env.get_owner_addresses()

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
        semaphore,
        seconds_per_epoch,
    ):
        super().__init__()
        self.slot = slot
        self.predictoor_contract = predictoor_contract
        self.current_ts = slot.slot

        self.nonce = nonce
        self.signature = None  # This will store the result
        self.semaphore = semaphore
        self.seconds_per_epoch = seconds_per_epoch

    def run(self) -> dict:
        """
        Get timestamp of previous epoch-2 , get the price
        Get timestamp of previous epoch-1, get the price
        Compare and submit trueval
        """
        self.semaphore.acquire()
        self.slot.slot = int(self.slot.slot)
        initial_ts = self.slot.slot - self.seconds_per_epoch
        end_ts = self.slot.slot

        (true_val, cancel_round) = get_true_val(self.slot.contract, initial_ts, end_ts)
        print(
            f"Contract:{self.predictoor_contract.contract_address} - Getting signature for true_val {true_val} and slot:{self.slot.slot}"
        )

        sig = self.predictoor_contract.trueval_sign(
            true_val, self.slot.slot, cancel_round, self.nonce
        )

        self.signature = {"signature": sig, "nonce": self.nonce}
        self.semaphore.release()


def process_slot(slot: Slot, nonce: int, semaphore) -> NewTrueVal:
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
    return NewTrueVal(slot, predictoor_contract, nonce, semaphore, seconds_per_epoch)


def main():
    while True:
        sleep_time = os.getenv("SLEEP_TIME", 15)
        pending_contracts = get_pending_slots(subgraph_url, web3_config)
        print(f"Found {len(pending_contracts)} pending slots")
        print("Owner addresses:", owner)
        nonce = web3_config.w3.eth.get_transaction_count(owner)
        print("Nonce:", nonce)
        threads = []
        results = []
        thread_limiter = threading.Semaphore(1)

        pending_contracts = pending_contracts[:2]

        if len(pending_contracts) > 0:
            # try:
            for slot in pending_contracts:
                sig = process_slot(slot, nonce, thread_limiter)
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
            signatures = [res["signature"] for res in sorted_signatures]

            # except Exception as e:
            #     print("An error occured while processing pending slots", e)
            print(f"Generated {len(signatures)} signatures")

            # execute all signatures
            print("Sending transactions...")
            for sig in signatures:
                print(sig)
                tx = web3_config.w3.eth.send_raw_transaction(sig.rawTransaction)
                print(f"Transaction {tx} sent")

        print("Sleeping for 15 seconds...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    main()
