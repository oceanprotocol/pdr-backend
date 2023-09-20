import math
import time
from typing import Dict, List

from enforce_typing import enforce_types
from pdr_backend.dfbuyer.dfbuyer_config import DFBuyerConfig
from pdr_backend.models.predictoor_batcher import PredictoorBatcher
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.token import Token
from pdr_backend.util.constants import MAX_UINT
from pdr_backend.util.contract import get_address
from pdr_backend.util.subgraph import get_consume_so_far_per_contract

WEEK = 7 * 86400


@enforce_types
class DFBuyerAgent:
    def __init__(self, config: DFBuyerConfig):
        self.config: DFBuyerConfig = config
        self.last_consume_ts = 0
        self.feeds = config.get_feeds()
        self.predictoor_batcher: PredictoorBatcher = PredictoorBatcher(
            self.config.web3_config,
            get_address(config.web3_config.w3.eth.chain_id, "PredictoorHelper"),
        )
        self.token_addr = get_address(config.web3_config.w3.eth.chain_id, "Ocean")

        print("-" * 80)
        print("Config:")
        print(self.config)

        print("\n" + "." * 80)
        print("Feeds (detailed):")
        for feed in self.feeds.values():
            print(f"  {feed.longstr()}")

        print("\n" + "." * 80)
        print("Feeds (succinct):")
        for addr, feed in self.feeds.items():
            print(f"  {feed}, {feed.seconds_per_epoch} s/epoch, addr={addr}")

        token = Token(self.config.web3_config, self.token_addr)
        print("Approving tokens for predictoor_batcher")
        tx = token.approve(
            self.predictoor_batcher.contract_address, int(MAX_UINT), True
        )
        print(f"Done: {tx['transactionHash'].hex()}")

    def run(self, testing: bool = False):
        while True:
            ts = self.config.web3_config.get_block("latest")["timestamp"]
            self.take_step(ts)

            if testing:
                break

    def take_step(self, ts: int):
        print("Taking step for timestamp:", ts)

        missing_consumes_amt = self._get_missing_consumes(ts)
        print("Missing consume amounts:", missing_consumes_amt)

        # get price for contracts with missing consume
        prices: Dict[str, float] = self._get_prices(list(missing_consumes_amt.keys()))

        missing_consumes_times: Dict[str, int] = {
            address: math.ceil(missing_consumes_amt[address] / prices[address])
            for address in missing_consumes_amt
        }
        print("Missing consume times:", missing_consumes_times)

        # batch txs
        self._batch_txs(missing_consumes_times)

        # sleep until next consume interval
        ts = self.config.web3_config.get_block("latest")["timestamp"]
        interval_start = (
            int(ts / self.config.consume_interval_seconds)
            * self.config.consume_interval_seconds
        )
        seconds_left = (interval_start + self.config.consume_interval_seconds) - ts
        print(
            f"-- Sleeping for {seconds_left} seconds until next consume interval... --"
        )
        time.sleep(seconds_left)

    def _get_missing_consumes(self, ts: int) -> Dict[str, float]:
        actual_consumes = self._get_consume_so_far(ts)
        expected_consume_per_feed = self._get_expected_amount_per_feed(ts)

        missing_consumes_amt: Dict[str, float] = {}

        for address in self.feeds:
            missing = expected_consume_per_feed - actual_consumes[address]
            if missing > 0:
                missing_consumes_amt[address] = missing

        return missing_consumes_amt

    def _prepare_batches(self, consume_times: Dict[str, int]):
        batches = []
        addresses_to_consume = []
        times_to_consume = []
        for address, times in consume_times.items():
            while times > 0:
                current_times_to_consume = min(
                    times, self.config.batch_size - sum(times_to_consume)
                )
                if current_times_to_consume > 0:
                    addresses_to_consume.append(
                        self.config.web3_config.w3.to_checksum_address(address)
                    )
                    times_to_consume.append(current_times_to_consume)
                    times -= current_times_to_consume
                if (
                    sum(times_to_consume) == self.config.batch_size
                    or address == list(consume_times.keys())[-1]
                ):
                    batches.append((addresses_to_consume, times_to_consume))
                    addresses_to_consume = []
                    times_to_consume = []
        return batches

    def _consume_batch(self, addresses_to_consume, times_to_consume):
        print(
            f"Consuming contracts {addresses_to_consume} for {times_to_consume} times."
        )
        for i in range(self.config.max_request_tries):
            try:
                tx = self.predictoor_batcher.consume_multiple(
                    addresses_to_consume,
                    times_to_consume,
                    self.token_addr,
                    True,
                )
                print("     Tx sent:", tx["transactionHash"].hex())
                break
            except Exception as e:
                print(f"     Attempt {i+1} failed with error: {e}")
                if i == 4:
                    print("     Failed to consume contracts after 5 attempts.")
                    raise

    def _batch_txs(self, consume_times: Dict[str, int]):
        batches = self._prepare_batches(consume_times)
        for addresses_to_consume, times_to_consume in batches:
            self._consume_batch(addresses_to_consume, times_to_consume)

    def _get_prices(self, contract_addresses: List[str]) -> Dict[str, float]:
        prices: Dict[str, float] = {}
        for address in contract_addresses:
            rate_wei = PredictoorContract(self.config.web3_config, address).get_price()
            rate_float = float(self.config.web3_config.w3.from_wei(rate_wei, "ether"))
            prices[address] = rate_float
        return prices

    def _get_consume_so_far(self, ts: int) -> Dict[str, float]:
        # TODO Update me to consider other dfbuyer instances
        week_start = (math.floor(ts / WEEK)) * WEEK
        consume_so_far = get_consume_so_far_per_contract(
            self.config.subgraph_url,
            self.config.web3_config.owner,
            week_start,
            list(self.feeds.keys()),
        )
        return consume_so_far

    def _get_expected_amount_per_feed(self, ts: int):
        amount_per_feed_per_interval = self.config.amount_per_interval / len(self.feeds)
        week_start = (math.floor(ts / WEEK)) * WEEK
        time_passed = ts - week_start

        # find out how many intervals has passed
        n_intervals = int(time_passed / self.config.consume_interval_seconds)

        return n_intervals * amount_per_feed_per_interval
