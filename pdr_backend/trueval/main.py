from datetime import datetime, timedelta, timezone
from threading import Thread
import time

from pdr_backend.trueval.trueval import get_true_val
from pdr_backend.utils.subgraph import get_all_interesting_prediction_contracts
from pdr_backend.utils.contract import PredictorContract, Web3Config
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
topics = []


class NewTrueVal(Thread):
    def __init__(self, topic, predictor_contract, current_block_num, epoch):
        # set a default value
        self.values = {
            "last_submited_epoch": epoch,
            "contract_address": predictor_contract.contract_address,
        }
        self.topic = topic
        self.epoch = epoch
        self.predictor_contract = predictor_contract
        self.current_block_num = current_block_num

    def run(self):
        """Get timestamp of previous epoch-2 , get the price"""
        """ Get timestamp of previous epoch-1, get the price """
        """ Compare and submit trueval """
        blocks_per_epoch = self.predictor_contract.get_blocksPerEpoch()
        initial_block = self.predictor_contract.get_block(
            (self.epoch - 2) * blocks_per_epoch
        )
        end_block = self.predictor_contract.get_block(
            (self.epoch - 1) * blocks_per_epoch
        )
        slot = (self.epoch - 1) * blocks_per_epoch

        (true_val, float_value, cancel_round) = get_true_val(
            self.topic, initial_block["timestamp"], end_block["timestamp"]
        )
        print(
            f"Contract:{self.predictor_contract.contract_address} - Submiting true_val {true_val} for slot:{slot}"
        )
        try:
            self.predictor_contract.submit_trueval(
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
        predictor_contract = PredictorContract(web3_config, address)
        epoch = predictor_contract.get_current_epoch()
        blocks_per_epoch = predictor_contract.get_blocksPerEpoch()
        blocks_till_epoch_end = (
            epoch * blocks_per_epoch + blocks_per_epoch - block["number"]
        )
        print(
            f"\t{topic['name']} (at address {topic['address']} is at epoch {epoch}, blocks_per_epoch: {blocks_per_epoch}, blocks_till_epoch_end: {blocks_till_epoch_end}"
        )
        if epoch > topic["last_submited_epoch"] and epoch > 1:
            """Let's make a prediction & claim rewards"""
            thr = NewTrueVal(topic, predictor_contract, block["number"], epoch)
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
