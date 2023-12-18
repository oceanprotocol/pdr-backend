from abc import ABC, abstractmethod
import time
from typing import List, Tuple

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.models.feed import print_feeds
from pdr_backend.util.mathutil import sole_value


class BasePredictoorAgent(ABC):

    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call get_prediction()
    """

    @enforce_types
    def __init__(self, ppss: PPSS):
        # ppss
        self.ppss = ppss
        print("\n" + "-" * 180)
        print(self.ppss)

        # set self.feeds
        cand_feeds = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        print(f"Filter by predict_feeds: {ppss.data_pp.filter_feeds_s}")
        feeds = ppss.data_pp.filter_feeds(cand_feeds)
        print_feeds(feeds, "filtered feeds")
        if not feeds:
            raise ValueError("No feeds found.")
        contracts = ppss.web3_pp.get_contracts(list(feeds.keys()))

        # set feed, contract
        self.feed = sole_value(feeds)
        self.feed_contract = sole_value(contracts)

        # set attribs to track block
        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0
        self.prev_submit_epochs: List[int] = []

    @enforce_types
    def run(self):
        print("Starting main loop.")
        print(self.status_str())
        print("Waiting...", end="")
        while True:
            self.take_step()

    @enforce_types
    def take_step(self):
        # at new block number yet?
        if self.cur_block_number <= self.prev_block_number:
            print(".", end="", flush=True)
            time.sleep(1)
            return

        # is new block ready yet?
        if not self.cur_block:
            return
        self.prev_block_number = self.cur_block_number
        self.prev_block_timestamp = self.cur_timestamp

        # within the time window to predict?
        if self.cur_epoch_s_left > self.epoch_s_thr:
            return

        print()
        print(self.status_str())

        # compute prediction; exit if no good
        submit_epoch, target_slot = self.cur_epoch, self.target_slot
        print(f"Predict for time slot = {self.target_slot}...")

        predval, stake = self.get_prediction(target_slot)
        print(f"-> Predict result: predval={predval}, stake={stake}")
        if predval is None or stake <= 0:
            print("Done: can't use predval/stake")
            return

        # submit prediction to chain
        print("Submit predict tx to chain...")
        self.feed_contract.submit_prediction(
            predval,
            stake,
            target_slot,
            wait_for_receipt=True,
        )
        self.prev_submit_epochs.append(submit_epoch)
        print("-> Submit predict tx result: success.")
        print("" + "=" * 180)

        # start printing for next round
        print(self.status_str())
        print("Waiting...", end="")

    @property
    def cur_epoch(self) -> int:
        return self.feed_contract.get_current_epoch()

    @property
    def cur_block(self):
        return self.ppss.web3_pp.web3_config.get_block(
            self.cur_block_number, full_transactions=False
        )

    @property
    def cur_block_number(self) -> int:
        return self.ppss.web3_pp.w3.eth.block_number

    @property
    def cur_timestamp(self) -> int:
        return self.cur_block["timestamp"]

    @property
    def epoch_s_thr(self):
        """Start predicting if there's > this time left"""
        return self.ppss.predictoor_ss.s_until_epoch_end

    @property
    def s_per_epoch(self) -> int:
        return self.feed.seconds_per_epoch

    @property
    def next_slot(self) -> int:  # a timestamp
        return (self.cur_epoch + 1) * self.s_per_epoch

    @property
    def target_slot(self) -> int:  # a timestamp
        return (self.cur_epoch + 2) * self.s_per_epoch

    @property
    def cur_epoch_s_left(self) -> int:
        return self.next_slot - self.cur_timestamp

    def status_str(self) -> str:
        s = ""
        s += f"cur_epoch={self.cur_epoch}"
        s += f", cur_block_number={self.cur_block_number}"
        s += f", cur_timestamp={self.cur_timestamp}"
        s += f", next_slot={self.next_slot}"
        s += f", target_slot={self.target_slot}"
        s += f". {self.cur_epoch_s_left} s left in epoch"
        s += f" (predict if <= {self.epoch_s_thr} s left)"
        s += f". s_per_epoch={self.s_per_epoch}"
        return s

    @abstractmethod
    def get_prediction(
        self,
        timestamp: int,  # pylint: disable=unused-argument
    ) -> Tuple[bool, float]:
        pass
