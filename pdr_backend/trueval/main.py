from threading import Thread
import time

from typing import Dict
from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.trueval.subgraph import get_pending_slots, Slot
from pdr_backend.utils.contract import PredictoorContract, Web3Config
from pdr_backend.utils import env


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


class NewTrueVal(Thread):
    def __init__(self, slot: Slot, predictoor_contract, epoch):
        # set a default value
        self.values = {
            "last_submited_epoch": epoch,
            "contract_address": predictoor_contract.address,
        }
        self.slot = slot
        self.epoch = epoch
        self.predictoor_contract = predictoor_contract
        self.current_ts = slot.slot

    def run(self, nonce: int):
        """
        Get timestamp of previous epoch-2 , get the price
        Get timestamp of previous epoch-1, get the price
        Compare and submit trueval
        """

        seconds_per_epoch = self.predictoor_contract.get_secondsPerEpoch()
        initial_ts = (self.epoch - 2) * seconds_per_epoch

        end_ts = (self.epoch - 1) * seconds_per_epoch

        slot = (self.epoch - 1) * seconds_per_epoch

        (true_val, float_value, cancel_round) = get_true_val(
            self.topic, initial_ts, end_ts
        )
        print(
            f"Contract:{self.predictoor_contract.address} - Submiting true_val {true_val} for slot:{slot}"
        )

        return self.predictoor_contract.trueval_sign(
            true_val, slot, float_value, cancel_round, nonce
        )


def process_slot(slot: Slot, nonce: int):
    predictoor_contract = PredictoorContract(web3_config, slot.contract.address)
    epoch = predictoor_contract.get_current_epoch()
    seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
    seconds_till_epoch_end = (
        epoch * seconds_per_epoch + seconds_per_epoch - epoch.slot
    )
    print(
        f"\t{slot.contract.name} (at address {slot.contract.address} is at epoch {slot.slot}, seconds_per_epoch: {seconds_per_epoch}, seconds_till_epoch_end: {seconds_till_epoch_end}"
    )

    thr = NewTrueVal(slot, predictoor_contract, epoch)
    signature = thr.run(nonce)
    return signature

def main():
    print("Starting main loop...")

    pending_contracts = get_pending_slots(subgraph_url, web3_config)
    nonce = web3_config.w3.eth.getTransactionCount(owner)
    signatures = []
    try:
        for slot in pending_contracts:
            nonce += 1
            sig = process_slot(slot, nonce)
            signatures.append(sig)
    except Exception as e:
        print("An error occured while processing pending slots", e)
    print(f"Generated {len(signatures)} signatures")
    # execute all signatures
    for sig in signatures:
        web3_config.w3.eth.sendRawTransaction(sig.rawTransaction)

    time.sleep(15)

    main()


if __name__ == "__main__":
    main()
