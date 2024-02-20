import logging
import os
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.contract.predictoor_batcher import PredictoorBatcher
from pdr_backend.contract.predictoor_contract import PredictoorContract
from pdr_backend.contract.slot import Slot
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.subgraph.subgraph_sync import wait_until_subgraph_syncs
from pdr_backend.trueval.get_trueval import get_trueval
from pdr_backend.util.logutil import logging_has_stdout
from pdr_backend.util.time_types import UnixTimeSeconds

logger = logging.getLogger("trueval_agent")


@enforce_types
class TruevalSlot(Slot):
    def __init__(self, slot_number: int, feed: SubgraphFeed):
        super().__init__(slot_number, feed)
        self.trueval: Optional[bool] = None
        self.cancel = False

    def set_trueval(self, trueval: Optional[bool]):
        self.trueval = trueval

    def set_cancel(self, cancel: bool):
        self.cancel = cancel


@enforce_types
class TruevalAgent:
    def __init__(self, ppss: PPSS, predictoor_batcher_addr: str):
        self.ppss = ppss
        self.predictoor_batcher: PredictoorBatcher = PredictoorBatcher(
            self.ppss.web3_pp, predictoor_batcher_addr
        )
        self.contract_cache: Dict[str, tuple] = {}

    def run(self, testing: bool = False):
        while True:
            self.take_step()
            if testing or os.getenv("TEST") == "true":
                break

    def take_step(self):
        wait_until_subgraph_syncs(
            self.ppss.web3_pp.web3_config, self.ppss.web3_pp.subgraph_url
        )
        pending_slots = self.get_batch()

        if len(pending_slots) == 0:
            logger.info(
                "No pending slots, sleeping for %d seconds...",
                self.ppss.trueval_ss.sleep_time,
            )
            time.sleep(self.ppss.trueval_ss.sleep_time)
            return

        # convert slots to TruevalSlot
        trueval_slots = [
            TruevalSlot(slot.slot_number, slot.feed) for slot in pending_slots
        ]

        # get the trueval for each slot
        for slot in trueval_slots:
            self.process_trueval_slot(slot)
            if logging_has_stdout():
                print(".", end="", flush=True)

        logger.debug("Submitting transaction...")

        tx_hash = self.batch_submit_truevals(trueval_slots)
        logger.info(
            "Tx sent: %s, sleeping for %d seconds...",
            tx_hash,
            self.ppss.trueval_ss.sleep_time,
        )

        time.sleep(self.ppss.trueval_ss.sleep_time)

    def get_batch(self) -> List[Slot]:
        timestamp = self.ppss.web3_pp.web3_config.get_block("latest")["timestamp"]

        pending_slots = self.ppss.web3_pp.get_pending_slots(
            timestamp,
            allowed_feeds=self.ppss.trueval_ss.feeds,
        )
        logger.info(
            "Found %d pending slots, processing %d",
            len(pending_slots),
            self.ppss.trueval_ss.batch_size,
        )
        pending_slots = pending_slots[: self.ppss.trueval_ss.batch_size]
        return pending_slots

    def get_contract_info(
        self, contract_address: str
    ) -> Tuple[PredictoorContract, int]:
        if contract_address in self.contract_cache:
            predictoor_contract, seconds_per_epoch = self.contract_cache[
                contract_address
            ]
        else:
            predictoor_contract = PredictoorContract(
                self.ppss.web3_pp, contract_address
            )
            seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
            self.contract_cache[contract_address] = (
                predictoor_contract,
                seconds_per_epoch,
            )
        return (predictoor_contract, seconds_per_epoch)

    def get_init_and_ts(
        self, slot: UnixTimeSeconds, seconds_per_epoch: int
    ) -> Tuple[UnixTimeSeconds, UnixTimeSeconds]:
        initial_ts = UnixTimeSeconds(slot - seconds_per_epoch)
        end_ts = UnixTimeSeconds(slot)
        return initial_ts, end_ts

    def get_trueval_slot(self, slot: Slot):
        """
        @description
          Get trueval at the specified slot

        @arguments
          slot

        @return
          trueval: bool
          cancel_round: bool
        """
        _, s_per_epoch = self.get_contract_info(slot.feed.address)
        init_ts, end_ts = self.get_init_and_ts(slot.slot_number, s_per_epoch)

        logger.info(
            "Get trueval slot: begin. For slot_number %d of %s",
            slot.slot_number,
            slot.feed,
        )
        try:
            # calls to get_trueval() func below, via Callable attribute on self
            (trueval, cancel_round) = get_trueval(slot.feed, init_ts, end_ts)
        except Exception as e:
            if "Too many requests" in str(e):
                logger.warning("Get trueval slot: too many requests, wait for a minute")
                time.sleep(60)
                return self.get_trueval_slot(slot)

            # pylint: disable=line-too-long
            raise Exception(f"An error occured: {e}") from e

        logger.info(
            "Get trueval slot: done. trueval=%s, cancel_round=%s", trueval, cancel_round
        )
        return (trueval, cancel_round)

    def batch_submit_truevals(self, slots: List[TruevalSlot]) -> str:
        contracts: dict = defaultdict(
            lambda: {"epoch_starts": [], "trueVals": [], "cancelRounds": []}
        )

        w3 = self.ppss.web3_pp.web3_config.w3
        for slot in slots:
            if slot.trueval is None:  # We only want slots with non-None truevals
                continue
            data = contracts[w3.to_checksum_address(slot.feed.address)]
            data["epoch_starts"].append(slot.slot_number)
            data["trueVals"].append(slot.trueval)
            data["cancelRounds"].append(slot.cancel)

        contract_addrs = list(contracts.keys())
        epoch_starts = [data["epoch_starts"] for data in contracts.values()]
        trueVals = [data["trueVals"] for data in contracts.values()]
        cancelRounds = [data["cancelRounds"] for data in contracts.values()]

        tx = self.predictoor_batcher.submit_truevals_contracts(
            contract_addrs, epoch_starts, trueVals, cancelRounds, True
        )
        return tx["transactionHash"].hex()

    def process_trueval_slot(self, slot: TruevalSlot):
        # (don't wrap with try/except because the called func already does)
        (trueval, cancel_round) = self.get_trueval_slot(slot)

        slot.set_trueval(trueval)
        if cancel_round:
            slot.set_cancel(True)
