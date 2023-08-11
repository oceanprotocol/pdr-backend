import time
import os
import math
import random

from pdr_backend.dfbuyer.subgraph import get_consume_so_far
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

last_block_time = 0
WEEK = 7 * 86400

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner


def numbers_with_sum(n, k):
    print(f"numbers_with_sum ({n},{k})")
    if n < 1:
        return []
    if n == 1:
        return [k]
    num = random.randint(1, k)
    return [num] + numbers_with_sum(n - 1, k - num)


""" Get all intresting topics that we can predict.  Like ETH-USDT, BTC-USDT """
topics = []
predictoor_contracts = []


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
    if len(topics) < 1:
        return
    # how many estimated blocks till end of week?
    estimated_week_start = (math.floor(block["timestamp"] / WEEK)) * WEEK
    print(f"estimated_week_start:{estimated_week_start}")
    # get consume so far
    consume_so_far = get_consume_so_far(topics, estimated_week_start, owner, subgraph_url)
    print(f"consume_so_far:{consume_so_far}")
    consume_left = float(os.getenv("WEEKLY_SPEND_LIMIT", 0)) - consume_so_far
    print(f"consume_left:{consume_left}")
    if consume_left <= 0:
        return
    estimated_week_end = estimated_week_start + WEEK
    print(f"estimated_week_end:{estimated_week_end}")
    estimated_time_left = estimated_week_end - estimated_week_start
    print(f"estimated_time_left:{estimated_time_left}")
    consume_target = random.uniform(0, consume_left / estimated_time_left * 100)
    print(f"consume_target:{consume_target}")
    # do random allocation
    buy_percentage_per_topic = numbers_with_sum(len(topics), 100)
    print(f"buy_percentage_per_topic:{buy_percentage_per_topic}")
    print(f"Got new block: {block['number']} with {len(topics)} topics")
    cnt = 0
    for address in topics:
        print(f"Percentage:{buy_percentage_per_topic[cnt]}")
        max_to_spend = consume_target * (buy_percentage_per_topic[cnt] / 100)
        predictoor_contract = PredictoorContract(web3_config, address)
        price = predictoor_contract.get_price() / 10**18
        txs = predictoor_contract.buy_many(
            int(max_to_spend / price), int(block["gasLimit"] * 0.99)
        )
        print(txs)
        cnt = cnt + 1


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
