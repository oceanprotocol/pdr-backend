import sys
import random
import time
from typing import Dict, List, Tuple

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.predictoor.approach1.predictoor_config1 import PredictoorConfig1


@enforce_types
class PredictoorAgent1:

    """
    What it does
    - Fetches Predictoor contracts from subgraph, and filters them
    - Monitors each contract for epoch changes.
    - When a value can be predicted, call predict.py::predict_function()
    """

    def __init__(self, config: PredictoorConfig1):
        self.config = config

        self.feeds: Dict[str, Feed] = self.config.get_feeds()  # [addr] : Feed

        if not self.feeds:
            print("No feeds found. Exiting")
            sys.exit()

        feed_addrs = list(self.feeds.keys())
        self.contracts = self.config.get_contracts(feed_addrs)  # [addr] : contract

        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0
        self.prev_submit_epochs_per_feed: Dict[str, List[int]] = {
            addr: [] for addr in self.feeds
        }

        print("\n" + "-" * 80)
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

    def run(self):
        print("Starting main loop...")
        while True:
            self.take_step()

    def take_step(self):
        w3 = self.config.web3_config.w3
        print("\n" + "-" * 80)
        print("Take_step() begin.")

        # new block?
        block_number = w3.eth.block_number
        print(f"  block_number={block_number}, prev={self.prev_block_number}")
        if block_number <= self.prev_block_number:
            print("  Done step: block_number hasn't advanced yet. So sleep.")
            time.sleep(1)
            return
        block = self.config.web3_config.get_block(block_number, full_transactions=False)
        if not block:
            print("  Done step: block not ready yet")
            return
        self.prev_block_number = block_number
        self.prev_block_timestamp = block["timestamp"]

        # do work at new block
        print("  Got new block. Timestamp={block['timestamp']}")
        for addr in self.feeds:
            self._process_block_at_feed(addr, block["timestamp"])

    def _process_block_at_feed(self, addr: str, timestamp: int) -> tuple:
        """Returns (predval, stake, submitted)"""
        # base data
        feed, contract = self.feeds[addr], self.contracts[addr]
        epoch = contract.get_current_epoch()
        s_per_epoch = feed.seconds_per_epoch
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp

        # print status
        print(f"    Process {feed} at epoch={epoch}")

        # within the time window to predict?
        print(
            f"      {epoch_s_left} s left in epoch"
            f" (predict if <= {self.config.s_until_epoch_end} s left)"
        )
        too_early = epoch_s_left > self.config.s_until_epoch_end
        if too_early:
            print("      Done feed: too early to predict")
            return (None, None, False)

        # compute prediction; exit if no good
        target_time = (epoch + 2) * s_per_epoch
        print(f"      Predict for time slot = {target_time}...")

        predval, stake = self.get_prediction(addr, target_time)
        print(f"      -> Predict result: predval={predval}, stake={stake}")
        if predval is None or stake <= 0:
            print("      Done feed: can't use predval/stake")
            return (None, None, False)

        # submit prediction to chain
        print("      Submit predict tx chain...")
        contract.submit_prediction(predval, stake, target_time, True)
        self.prev_submit_epochs_per_feed[addr].append(epoch)
        print("      " + "=" * 80)
        print("      -> Submit predict tx result: success.")
        print("      " + "=" * 80)
        print("      Done feed: success.")
        return (predval, stake, True)

    def get_prediction(
        self, addr: str, timestamp: int  # pylint: disable=unused-argument
    ) -> Tuple[bool, int]:
        """
        @description
          Given a feed, let's predict for a given timestamp.

        @arguments
          addr -- str -- address of the trading pair. Info in self.feeds[addr]
          timestamp -- int -- when to make prediction for (unix time)

        @return
          predval -- bool -- if True, it's predicting 'up'. If False, 'down'
          stake -- int -- amount to stake, in units of wei

        @notes
          Below is the default implementation, giving random predictions.
          You need to customize it to implement your own strategy.
        """
        # Pick random prediction & random stake. You need to customize this.
        predval = bool(random.getrandbits(1))
        stake = random.randint(1, 10) / 1000

        return (predval, stake)
