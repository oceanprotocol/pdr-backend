from datetime import datetime, timedelta, timezone
import os
from os import getenv
import time
import threading
from threading import Thread
from typing import Dict

from pdr_backend.predictoor.approach1.predict import predict_function
from pdr_backend.utils.env import get_envvar_or_exit
from pdr_backend.utils.contract import PredictoorContract, Web3Config
from pdr_backend.utils.subgraph import get_all_interesting_prediction_contracts

last_block_time = 0
topics: Dict[str, dict] = {}
contract_map: Dict[str, PredictoorContract] = {}

rpc_url = get_envvar_or_exit("RPC_URL")
subgraph_url = get_envvar_or_exit("SUBGRAPH_URL")
private_key = get_envvar_or_exit("PRIVATE_KEY")
pair_filters = getenv("PAIR_FILTER")
timeframe_filter = getenv("TIMEFRAME_FILTER")
source_filter = getenv("SOURCE_FILTER")
owner_addresses = getenv("OWNER_ADDRS")

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner


def process_block(block):
    global topics
    """ Process each contract and if needed, get a prediction, submit it and claim revenue for past epoch """
    if not topics:
        topics = get_all_interesting_prediction_contracts(
            subgraph_url,
            pair_filters,
            timeframe_filter,
            source_filter,
            owner_addresses,
        )
    print(f"Got new block: {block['number']} with {len(topics)} topics")
    for address in topics:
        topic = topics[address]
        if contract_map.get(address) is None:
            contract_map[address] = PredictoorContract(web3_config, address)
        predictoor_contract = contract_map[address]
        epoch = predictoor_contract.get_current_epoch()
        seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
        seconds_till_epoch_end = (
            epoch * seconds_per_epoch + seconds_per_epoch - block["timestamp"]
        )
        print(
            f"\t{topic['name']} (at address {topic['address']} is at epoch {epoch}, seconds_per_epoch: {seconds_per_epoch}, seconds_till_epoch_end: {seconds_till_epoch_end}"
        )

        if epoch > topic["last_submited_epoch"] and topic["last_submited_epoch"] > 0:
            # let's get the payout for previous epoch.  We don't care if it fails...
            slot = epoch * seconds_per_epoch - seconds_per_epoch
            print(
                f"Contract:{predictoor_contract.contract_address} - Claiming revenue for slot:{slot}"
            )
            predictoor_contract.payout(slot, False)

        if seconds_till_epoch_end <= int(getenv("SECONDS_TILL_EPOCH_END", 60)):
            """Timestamp of prediction"""
            target_time = (epoch + 2) * seconds_per_epoch

            """Let's fetch the prediction """
            (predicted_value, predicted_confidence) = predict_function(
                topic, target_time
            )
            if predicted_value is not None and predicted_confidence > 0:
                """We have a prediction, let's submit it"""
                stake_amount = (
                    getenv("STAKE_AMOUNT", 1) * predicted_confidence / 100
                )  # TODO have a customizable function to handle this
                print(
                    f"Contract:{predictoor_contract.contract_address} - Submiting prediction for slot:{target_time}"
                )
                predictoor_contract.submit_prediction(
                    predicted_value, stake_amount, target_time, True
                )
                topics[address]["last_submited_epoch"] = epoch
            else:
                print(
                    f"We do not submit, prediction function returned ({predicted_value}, {predicted_confidence})"
                )


def log_loop(blockno):
    global last_block_time
    block = web3_config.w3.eth.get_block(blockno, full_transactions=False)
    if block:
        last_block_time = block["timestamp"]
        process_block(block)


def main():
    print("Starting main loop...")
    lastblock = 0
    while True:
        block = web3_config.w3.eth.block_number
        if block > lastblock:
            lastblock = block
            log_loop(block)
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
