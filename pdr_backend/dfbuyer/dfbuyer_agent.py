import logging
import math
import os
import time
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_consume_so_far import get_consume_so_far_per_contract
from pdr_backend.subgraph.subgraph_feed import print_feeds
from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs
from pdr_backend.util.constants import MAX_UINT
from pdr_backend.util.mathutil import from_wei

WEEK = 7 * 86400
logger = logging.getLogger(__name__)


@enforce_types
class DFBuyerAgent:
    def __init__(self, ppss: PPSS):
        # ppss
        self.ppss = ppss
        logger.info(self.ppss)

        # set self.feeds
        cand_feeds = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"all feeds, owner={ppss.web3_pp.owner_addrs}")

        self.feeds = ppss.dfbuyer_ss.filter_feeds_from_candidates(cand_feeds)

        if not self.feeds:
            raise ValueError("No feeds found.")

        # addresses
        batcher_addr = ppss.web3_pp.get_address("PredictoorHelper")
        self.OCEAN_addr = ppss.web3_pp.get_address("Ocean")

        # set attribs to track progress
        self.last_consume_ts = 0
        self.predictoor_batcher: PredictoorBatcher = PredictoorBatcher(
            ppss.web3_pp,
            batcher_addr,
        )
        self.fail_counter = 0
        self.batch_size = ppss.dfbuyer_ss.batch_size

        # Check allowance and approve if necessary
        logger.info("Checking allowance...")
        OCEAN = ppss.web3_pp.OCEAN_Token
        allowance = OCEAN.allowance(
            ppss.web3_pp.web3_config.owner,
            self.predictoor_batcher.contract_address,
        )
        if allowance < MAX_UINT - 10**50:
            logger.info("Approving tokens for predictoor_batcher")
            tx = OCEAN.approve(
                self.predictoor_batcher.contract_address, int(MAX_UINT), True
            )
            logger.info(f"Done: {tx['transactionHash'].hex()}")

    def run(self, testing: bool = False):
        if not self.feeds:
            return

        while True:
            ts = self.ppss.web3_pp.web3_config.get_current_timestamp()
            self.take_step(ts)

            if testing or os.getenv("TEST") == "true":
                break

    def take_step(self, ts: int):
        if not self.feeds:
            return

        logger.info("Taking step for timestamp: %s", ts)
        wait_until_subgraph_syncs(
            self.ppss.web3_pp.web3_config, self.ppss.web3_pp.subgraph_url
        )
        missing_consumes_amt = self._get_missing_consumes(ts)
        logger.info("Missing consume amounts: %s", missing_consumes_amt)

        # get price for contracts with missing consume
        prices: Dict[str, float] = self._get_prices(list(missing_consumes_amt.keys()))
        missing_consumes_times = self._get_missing_consume_times(
            missing_consumes_amt, prices
        )
        logger.info("Missing consume times: %s", missing_consumes_times)

        # batch txs
        one_or_more_failed = self._batch_txs(missing_consumes_times)

        if one_or_more_failed:
            logger.info("One or more consumes have failed...")
            self.fail_counter += 1

            batch_size = self.ppss.dfbuyer_ss.batch_size
            if self.fail_counter > 3 and batch_size > 6:
                self.batch_size = batch_size * 2 // 3
                logger.warning(
                    "Seems like we keep failing, adjusting batch size to: %d",
                    batch_size,
                )
                self.fail_counter = 0

            logger.info("Sleeping for a minute and trying again")
            time.sleep(60)
            return

        self.fail_counter = 0
        self._sleep_until_next_consume_interval()

    def _sleep_until_next_consume_interval(self):
        # sleep until next consume interval
        ts = self.ppss.web3_pp.web3_config.get_current_timestamp()
        consume_interval_seconds = self.ppss.dfbuyer_ss.consume_interval_seconds

        interval_start = int(ts / consume_interval_seconds) * consume_interval_seconds
        seconds_left = (interval_start + consume_interval_seconds) - ts + 60

        logger.info("Sleeping for %d seconds until next consume interval", seconds_left)
        time.sleep(seconds_left)

    def _get_missing_consume_times(
        self, missing_consumes: Dict[str, float], prices: Dict[str, float]
    ) -> Dict[str, int]:
        return {
            address: math.ceil(missing_consumes[address] / prices[address])
            for address in missing_consumes
        }

    def _get_missing_consumes(self, ts: int) -> Dict[str, float]:
        actual_consumes = self._get_consume_so_far(ts)
        expected_consume_per_feed = self._get_expected_amount_per_feed(ts)

        return {
            address: expected_consume_per_feed - actual_consumes[address]
            for address in self.feeds
            if expected_consume_per_feed > actual_consumes[address]
        }

    def _prepare_batches(
        self, consume_times: Dict[str, int]
    ) -> List[Tuple[List[str], List[int]]]:
        batch_size = self.ppss.dfbuyer_ss.batch_size

        max_no_of_addresses_in_batch = 3  # to avoid gas issues
        batches: List[Tuple[List[str], List[int]]] = []
        addresses_to_consume: List[str] = []
        times_to_consume: List[int] = []

        for address, times in consume_times.items():
            while times > 0:
                current_times_to_consume = min(
                    times, batch_size - sum(times_to_consume)
                )
                if current_times_to_consume > 0:
                    addresses_to_consume.append(
                        self.ppss.web3_pp.web3_config.w3.to_checksum_address(address)
                    )
                    times_to_consume.append(current_times_to_consume)
                    times -= current_times_to_consume
                if (
                    sum(times_to_consume) == batch_size
                    or address == list(consume_times.keys())[-1]
                    or len(addresses_to_consume) == max_no_of_addresses_in_batch
                ):
                    batches.append((addresses_to_consume, times_to_consume))
                    addresses_to_consume = []
                    times_to_consume = []

        return batches

    def _consume(self, addresses_to_consume, times_to_consume):
        for i in range(self.ppss.dfbuyer_ss.max_request_tries):
            try:
                tx = self.predictoor_batcher.consume_multiple(
                    addresses_to_consume,
                    times_to_consume,
                    self.OCEAN_addr,
                    True,
                )
                tx_hash = tx["transactionHash"].hex()

                if tx["status"] != 1:
                    logger.warning(f"Tx reverted: %s", tx_hash)
                    return False

                logger.info("Tx sent: %s", tx_hash)
                return True
            except Exception as e:
                logger.warning("Attempt %d failed with error: %s", i + 1, e)
                time.sleep(1)

                if i == 4:
                    logger.error("Failed to consume contracts after 5 attempts.")
                    raise

        return False

    def _consume_batch(self, addresses_to_consume, times_to_consume) -> bool:
        one_or_more_failed = False
        logger.info(
            "Consuming contracts %s for %s times.",
            addresses_to_consume,
            times_to_consume,
        )

        # Try to consume the batch
        if self._consume(addresses_to_consume, times_to_consume):
            return False  # If successful, return False (no failures)

        # If batch consumption fails, fall back to consuming one by one
        logger.warning("Transaction reverted, consuming one by one...")
        for address, times in zip(addresses_to_consume, times_to_consume):
            if self._consume([address], [times]):
                continue  # If successful, continue to the next address

            # If individual consumption fails, split the consumption into two parts
            half_time = times // 2

            if half_time > 0:
                logger.info("Consuming %s for %s times", address, half_time)
                if not self._consume([address], [half_time]):
                    logger.error("Transaction reverted again, please adjust batch size")
                    one_or_more_failed = True

                remaining_times = times - half_time
                if remaining_times > 0:
                    logger.info("Consuming %s for %s times", address, remaining_times)
                    if not self._consume([address], [remaining_times]):
                        logger.error(
                            "Transaction reverted again, please adjust batch size"
                        )
                        one_or_more_failed = True
            else:
                logger.error("Unable to consume %s for %s times", address, times)
                one_or_more_failed = True

        return one_or_more_failed

    def _batch_txs(self, consume_times: Dict[str, int]) -> bool:
        batches = self._prepare_batches(consume_times)
        logger.info("Processing %s batches", len(batches))

        failures = 0

        for addresses_to_consume, times_to_consume in batches:
            failures += int(self._consume_batch(addresses_to_consume, times_to_consume))

        return bool(failures)

    def _get_prices(self, contract_addresses: List[str]) -> Dict[str, float]:
        return {
            address: from_wei(
                PredictoorContract(self.ppss.web3_pp, address).get_price()
            )
            for address in contract_addresses
        }

    def _get_consume_so_far(self, ts: int) -> Dict[str, float]:
        week_start = (math.floor(ts / WEEK)) * WEEK
        consume_so_far = get_consume_so_far_per_contract(
            self.ppss.web3_pp.subgraph_url,
            self.ppss.web3_pp.web3_config.owner,
            week_start,
            list(self.feeds.keys()),
        )
        return consume_so_far

    def _get_expected_amount_per_feed(self, ts: int):
        ss = self.ppss.dfbuyer_ss
        amount_per_feed_per_interval = ss.amount_per_interval / len(self.feeds)
        week_start = (math.floor(ts / WEEK)) * WEEK
        time_passed = ts - week_start

        # find out how many intervals has passed
        n_intervals = int(time_passed / ss.consume_interval_seconds) + 1

        return n_intervals * amount_per_feed_per_interval
