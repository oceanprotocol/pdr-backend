import time
from os import getenv
import math
import random
from typing import Dict, List

from pdr_backend.dfbuyer.subgraph import get_consume_so_far
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.subgraph import query_predictContracts
from pdr_backend.util.web3_config import Web3Config

rpc_url = getenv_or_exit("RPC_URL")
subgraph_url = getenv_or_exit("SUBGRAPH_URL")
private_key = getenv_or_exit("PRIVATE_KEY")
pair_filters = getenv("PAIR_FILTER")
timeframe_filter = getenv("TIMEFRAME_FILTER")
source_filter = getenv("SOURCE_FILTER")
owner_addresses = getenv("OWNER_ADDRS")

last_block_time = 0
WEEK = 7 * 86400

web3_config = Web3Config(rpc_url, private_key)
owner = web3_config.owner


def numbers_with_sum(n: int, k: int) -> List[int]:
    """
    Generate a list of n integers that sum up to k.

    @param:
        n - Number of integers to generate.
        k - The total sum of the generated integers.

    @return:
        A list of n integers that sum up to k.
    """

    # If n is 1, the only possible list is [k].
    if n < 1:
        return []
    if n == 1:
        return [k]
    # If n > k, it's impossible to generate n positive integers summing to k.
    if n > k:
        return []

    # Generate n-1 unique random integers between 1 and k-1
    a = random.sample(range(1, k), n - 1)

    # Add 0 and k to the list
    a.extend([0, k])
    a.sort()

    # Calculate the difference between consecutive numbers and output
    return [a[i + 1] - a[i] for i in range(len(a) - 1)]


# Get all intresting topics that we can predict.  Like ETH-USDT, BTC-USDT
topics: Dict[str, dict] = {}


def process_block(block):
    """Process each contract and see if we need to submit"""
    global topics
    if not topics:
        topics = query_predictContracts(
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
    consume_so_far = get_consume_so_far(
        topics, estimated_week_start, owner, subgraph_url
    )
    print(f"consume_so_far:{consume_so_far}")
    consume_left = float(getenv("WEEKLY_SPEND_LIMIT", "0")) - consume_so_far
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
