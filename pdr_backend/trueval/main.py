from datetime import datetime, timedelta, timezone
from threading import Thread
import time

from typing import Dict
from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.utils.subgraph import get_all_interesting_prediction_contracts
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
    def __init__(self, topic, predictoor_contract, current_ts, epoch):
        # set a default value
        self.values = {
            "last_submited_epoch": epoch,
            "contract_address": predictoor_contract.contract_address,
        }
        self.topic = topic
        self.epoch = epoch
        self.predictoor_contract = predictoor_contract
        self.current_ts = current_ts

    def run(self):
        """Get timestamp of previous epoch-2 , get the price"""
        """ Get timestamp of previous epoch-1, get the price """
        """ Compare and submit trueval """
        seconds_per_epoch = self.predictoor_contract.get_secondsPerEpoch()
        initial_ts = (self.epoch - 2) * seconds_per_epoch

        end_ts = (self.epoch - 1) * seconds_per_epoch

        slot = (self.epoch - 1) * seconds_per_epoch

        (true_val, float_value, cancel_round) = get_true_val(
            self.topic, initial_ts, end_ts
        )
        print(
            f"Contract:{self.predictoor_contract.contract_address} - Submiting true_val {true_val} for slot:{slot}"
        )
        try:
            self.predictoor_contract.submit_trueval(
                true_val, slot, float_value, cancel_round
            )
        except Exception as e:
            print(e)
            pass


def process_block(block):
    global topics
    """ Process each contract and see if we need to submit """
    if not topics:
        topics = get_all_interesting_prediction_contracts(
            subgraph_url,
            pair_filters,
            timeframe_filter,
            source_filter,
            owner_addresses,
        )
    print(f"Got new block: {block['number']} with {len(topics)} topics")
    threads = []
    for address in topics:
        topic = topics[address]
        predictoor_contract = PredictoorContract(web3_config, address)
        epoch = predictoor_contract.get_current_epoch()
        seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
        seconds_till_epoch_end = (
            epoch * seconds_per_epoch + seconds_per_epoch - block["timestamp"]
        )
        print(
            f"\t{topic['name']} (at address {topic['address']} is at epoch {epoch}, seconds_per_epoch: {seconds_per_epoch}, seconds_till_epoch_end: {seconds_till_epoch_end}"
        )
        if epoch > topic["last_submited_epoch"] and epoch > 1:
            """Let's make a prediction & claim rewards"""
            thr = NewTrueVal(topic, predictoor_contract, block["timestamp"], epoch)
            thr.run()
            address = thr.values["contract_address"].lower()
            new_epoch = thr.values["last_submited_epoch"]
            topics[address]["last_submited_epoch"] = new_epoch


def main():
    print("Starting main loop...")
    lastblock = 0
    while True:
        block = web3_config.w3.eth.block_number
        if block > lastblock:
            lastblock = block
            process_block(web3_config.w3.eth.get_block(block, full_transactions=False))
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
