from collections import defaultdict
import time
from typing import List, Optional, Tuple, Callable

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_batcher import PredictoorBatcher
from pdr_backend.models.slot import Slot
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.trueval.trueval_agent_base import TruevalAgentBase
from pdr_backend.util.subgraph import wait_until_subgraph_syncs


@enforce_types
class TruevalSlot(Slot):
    def __init__(self, slot_number: int, feed: Feed):
        super().__init__(slot_number, feed)
        self.trueval: Optional[bool] = None
        self.cancel = False

    def set_trueval(self, trueval: Optional[bool]):
        self.trueval = trueval

    def set_cancel(self, cancel: bool):
        self.cancel = cancel


@enforce_types
class TruevalAgentBatch(TruevalAgentBase):
    def __init__(
        self,
        ppss: PPSS,
        _get_trueval: Callable[[Feed, int, int], Tuple[bool, bool]],
        predictoor_batcher_addr: str,
    ):
        super().__init__(ppss, _get_trueval)
        self.predictoor_batcher: PredictoorBatcher = PredictoorBatcher(
            self.ppss.web3_pp, predictoor_batcher_addr
        )

    def take_step(self):
        wait_until_subgraph_syncs(
            self.ppss.web3_pp.web3_config, self.ppss.web3_pp.subgraph_url
        )
        pending_slots = self.get_batch()

        if len(pending_slots) == 0:
            print(
                f"No pending slots, sleeping for {self.ppss.trueval_ss.sleep_time} seconds..."
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
            print(".", end="", flush=True)
        print()  # new line

        print("Submitting transaction...")

        tx_hash = self.batch_submit_truevals(trueval_slots)
        print(
            f"Tx sent: {tx_hash}, sleeping for {self.ppss.trueval_ss.sleep_time} seconds..."
        )

        time.sleep(self.ppss.trueval_ss.sleep_time)

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
