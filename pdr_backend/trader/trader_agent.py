import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.trader.trader_config import TraderConfig
from pdr_backend.util.cache import Cache


MAX_TRIES = 10


# pylint: disable=too-many-instance-attributes
class TraderAgent:
    def __init__(
        self,
        trader_config: TraderConfig,
        _do_trade: Optional[Callable[[Feed, Tuple], Any]] = None,
        cache_dir=".cache",
    ):
        self.config = trader_config
        self._do_trade = _do_trade if _do_trade else do_trade

        self.feeds: Dict[str, Feed] = self.config.get_feeds()  # [addr] : Feed

        if not self.feeds:
            print("No feeds found. Exiting")
            sys.exit()

        feed_addrs = list(self.feeds.keys())
        self.contracts = self.config.get_contracts(feed_addrs)  # [addr] : contract

        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0

        self.prev_traded_epochs_per_feed: Dict[str, List[int]] = {
            addr: [] for addr in self.feeds
        }

        self.cache = Cache(cache_dir=cache_dir)
        self.load_cached_epochs()

    def save_previous_epochs(self):
        for feed, epochs in self.prev_traded_epochs_per_feed.items():
            if epochs:
                last_epoch = epochs[-1]
                print("Saving", last_epoch, feed)
                self.cache.save(f"trader_last_trade_{feed}", last_epoch)

    def load_cached_epochs(self):
        for feed in self.feeds:
            print("Getting feed for", feed)
            last_epoch = self.cache.load(f"trader_last_trade_{feed}")
            if last_epoch is not None:
                self.prev_traded_epochs_per_feed[feed].append(last_epoch)

    @enforce_types
    def run(self, testing: bool = False):
        while True:
            self.take_step()
            if testing:
                break

    def take_step(self):
        w3 = self.config.web3_config.w3

        # at new block number yet?
        block_number = w3.eth.block_number
        if block_number <= self.prev_block_number:
            time.sleep(1)
            return
        self.prev_block_number = block_number

        # is new block ready yet?
        block = self.config.web3_config.get_block(block_number, full_transactions=False)
        if not block:
            return

        self.prev_block_number = block_number
        self.prev_block_timestamp = block["timestamp"]

        s_till_epoch_ends = []

        # do work at new block
        for addr in self.feeds:
            s_till_epoch_ends.append(
                self._process_block_at_feed(addr, block["timestamp"])
            )

        sleep_time = min(s_till_epoch_ends) - 1
        print(f"-- Soonest epoch is in {sleep_time} seconds, waiting... --")
        time.sleep(sleep_time)

    def _process_block_at_feed(self, addr: str, timestamp: int, tries: int = 0) -> int:
        """
        @param:
            addr - contract address of the feed
            timestamp - timestamp/epoch to process
            [tries] - number of attempts made in case of an error, 0 by default
        @return:
            epoch_s_left - number of seconds left till the epoch end
        """
        feed, predictoor_contract = self.feeds[addr], self.contracts[addr]

        s_per_epoch = feed.seconds_per_epoch
        epoch = int(timestamp / s_per_epoch)
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp

        # print status
        print(
            f"{feed.name} at address {addr}"
            f" is at epoch {epoch}"
            f". s_per_epoch: {s_per_epoch}, "
            f"s_remaining_in_epoch: {epoch_s_left}"
        )

        if (
            self.prev_traded_epochs_per_feed.get(addr)
            and epoch == self.prev_traded_epochs_per_feed[addr][-1]
        ):
            print("      Done feed: already traded this epoch")
            return epoch_s_left

        if epoch_s_left < self.config.trader_min_buffer:
            print("      Done feed: not enough time left in epoch")
            return epoch_s_left

        try:
            prediction = predictoor_contract.get_agg_predval((epoch + 1) * s_per_epoch)
        except Exception as e:
            if tries < MAX_TRIES:
                print("     Could not get aggpredval, trying again in a second")
                time.sleep(1)
                return self._process_block_at_feed(addr, timestamp, tries + 1)
            print("      Done feed: aggpredval not available, an error occured:", e)
            return epoch_s_left

        print(f"Got {prediction}.")

        self._do_trade(feed, prediction)
        self.prev_traded_epochs_per_feed[addr].append(epoch)
        self.save_previous_epochs()
        return epoch_s_left


def do_trade(feed: Feed, prediction: Tuple[float, float]):
    """
    @description
        This function is called each time there's a new prediction available.
        By default, it prints the signal.
        The user should implement their trading algorithm here.
    @params
        feed : Feed
            An instance of the Feed object.

        prediction : Tuple[float, float]
            A tuple containing two float values, the unit is ETH:
            - prediction[0]: Amount staked for the price going up.
            - prediction[1]: Total stake amount.
    @note
        The probability of the price going up is determined by dividing
        prediction[0] by prediction[1]. The magnitude of stake amounts indicates
        the confidence of the prediction. Ensure stake amounts
        are sufficiently large to be considered meaningful.
    """
    pred_nom, pred_denom = prediction
    print(
        f" {feed.name} (contract {feed.address}) "
        f"has a new prediction: {pred_nom} / {pred_denom}.  Let's buy or sell"
    )
    # Trade here
    # ...
