from os import getenv
import time
from typing import Dict

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.trade import trade
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.subgraph import query_feed_contracts
from pdr_backend.util.web3_config import Web3Config

rpc_url = getenv_or_exit("RPC_URL")
subgraph_url = getenv_or_exit("SUBGRAPH_URL")
private_key = getenv_or_exit("PRIVATE_KEY")
pair_filters = getenv("PAIR_FILTER")
timeframe_filter = getenv("TIMEFRAME_FILTER")
source_filter = getenv("SOURCE_FILTER")
owner_addresses = getenv("OWNER_ADDRS")

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner


# Get all intresting topics that we can predict.  Like ETH-USDT, BTC-USDT
topics: Dict[str, dict] = {}


def process_block(block):
    """Process each contract and see if we need to submit"""
    global topics
    if not topics:
        topics = query_feed_contracts(
            subgraph_url,
            pair_filters,
            timeframe_filter,
            source_filter,
            owner_addresses,
        )
    print(f"Got new block: {block['number']} with {len(topics)} topics")
    for address in topics:
        topic = topics[address]
        predictoor_contract = PredictoorContract(web3_config, address)
        epoch = predictoor_contract.get_current_epoch()
        seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
        seconds_till_epoch_end = (
            epoch * seconds_per_epoch + seconds_per_epoch - block["timestamp"]
        )
        print(
            f"\t{topic['name']} (at address {topic['address']} "
            f"is at epoch {epoch}, seconds_per_epoch: {seconds_per_epoch}"
            f", seconds_till_epoch_end: {seconds_till_epoch_end}"
        )
        if epoch > topic["last_submited_epoch"] and epoch > 0:
            topic["last_submited_epoch"] = epoch
            print("Read new prediction")
            # Let's get the prediction and trade it
            prediction = predictoor_contract.get_agg_predval(epoch * seconds_per_epoch)
            print(f"Got {prediction}.")
            if prediction is not None:
                trade(topic, prediction)


def main():
    print("Starting main loop...")
    lastblock = 0
    while True:
        block = web3_config.w3.eth.block_number
        if block > lastblock:
            lastblock = block
            process_block(web3_config.get_block(block, full_transactions=False))
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
