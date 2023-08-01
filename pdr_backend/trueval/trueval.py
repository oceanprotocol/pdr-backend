"""
Flow
  - reads from subgraph list of template3 contracts, this gets list of all template3 deployed contracts
  - for every contract, monitors when epoch is changing
  - once an epoch is ended, calculate the true_val and submit.

Notes on customization:

  The actual true_val is fetched by calling function get_true_val()

  We call get_true_val() with 4 args:
   - topic: this is pair object
   - initial_timestamp:   blocktime for begining of epoch - 2
   - end_timestamp:   blocktime for begining of epoch -1

  Then it returns true_val, which gets submitted to contract

  You need to change the code to support more complex flows. Now, it's based on ccxt
"""

from datetime import datetime, timedelta, timezone
from threading import Thread
import time
import os

import ccxt

from pdr_backend.utils.subgraph import get_all_interesting_prediction_contracts
from pdr_backend.utils.contract import PredictorContract, Web3Config

# TODO - check for all envs
assert os.environ.get("RPC_URL", None), "You must set RPC_URL environment variable"
assert os.environ.get(
    "SUBGRAPH_URL", None
), "You must set SUBGRAPH_URL environment variable"
web3_config = Web3Config(os.environ.get("RPC_URL"), os.environ.get("PRIVATE_KEY"))
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
            os.environ.get("SUBGRAPH_URL"),
            os.environ.get("PAIR_FILTER", None),
            os.environ.get("TIMEFRAME_FILTER", None),
            os.environ.get("SOURCE_FILTER", None),
            os.environ.get("OWNER_ADDRS", None),
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


def trueval_main():
    print("Starting main loop...")
    lastblock = 0
    while True:
        block = web3_config.w3.eth.block_number
        if block > lastblock:
            lastblock = block
            process_block(web3_config.w3.eth.get_block(block, full_transactions=False))
        else:
            time.sleep(1)



def get_true_val(topic, initial_timestamp, end_timestamp):
    """Given a topic, Returns the true val between end_timestamp and initial_timestamp
    Topic object looks like:

    {
        "name":"ETH-USDT",
        "address":"0x54b5ebeed85f4178c6cb98dd185067991d058d55",
        "symbol":"ETH-USDT",
        "blocks_per_epoch":"60",
        "blocks_per_subscription":"86400",
        "last_submited_epoch":0,
        "pair":"eth-usdt",
        "base":"eth",
        "quote":"usdt",
        "source":"kraken",
        "timeframe":"5m"
    }

    """
    try:
        exchange_class = getattr(ccxt, topic["source"])
        exchange_ccxt = exchange_class()
        price_initial = exchange_ccxt.fetch_ohlcv(
            topic["pair"], "1m", since=initial_timestamp, limit=1
        )
        price_end = exchange_ccxt.fetch_ohlcv(
            topic["pair"], "1m", since=end_timestamp, limit=1
        )
        return (price_end[0][1] >= price_initial[0][1], price_end[0][1], False)
    except Exception as e:
        return (False, 0, True)
