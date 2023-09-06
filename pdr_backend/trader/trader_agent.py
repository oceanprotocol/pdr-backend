import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.trader.trader_config import TraderConfig


class TraderAgent:
    def __init__(
        self,
        trader_config: TraderConfig,
        _get_trader: Optional[Callable[[Feed, int], Any]] = None,
    ):
        self.config = trader_config
        self._get_trader = _get_trader if _get_trader else get_trader

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
            return None
        self.prev_block_number = block_number

        # is new block ready yet?
        block = self.config.web3_config.get_block(block_number, full_transactions=False)
        if not block:
            return None

        self.prev_block_number = block_number
        self.prev_block_timestamp = block["timestamp"]
        print(f"Got new block, with number {block_number} ")

        # do work at new block
        for addr in self.feeds:
            return self._process_block_at_feed(addr, block["timestamp"])

    def _process_block_at_feed(self, addr: str, timestamp: int) -> Any:
        # base data
        feed, predictoor_contract = self.feeds[addr], self.contracts[addr]
        epoch = predictoor_contract.get_current_epoch()
        s_per_epoch = feed.seconds_per_epoch
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp

        too_early = epoch_s_left > self.config.s_until_epoch_end
        if too_early:
            print("      Done feed: too early to trade")
            return None

        # print status
        print(
            f"{feed.name} at address {addr}"
            f" is at epoch {epoch}"
            f". s_per_epoch: {s_per_epoch}, "
            f"s_remaining_in_epoch: {epoch_s_left}"
        )

        prediction = predictoor_contract.get_agg_predval(epoch * s_per_epoch)
        print(f"Got {prediction}.")
        if prediction[0] is not None and prediction[1] is not None:
            trade_result = self._get_trader(feed, prediction)
            self.prev_traded_epochs_per_feed[addr].append(epoch)
            return trade_result

        return None


def get_trader(feed: Feed, prediction: Tuple) -> Optional[Any]:
    pred_nom, pred_denom = prediction
    print(
        f" {feed.name} (contract {feed.address}) "
        f"has a new prediction: {pred_nom} / {pred_denom}.  Let's buy or sell"
    )
    # Do your things here
    # ...
    # return anything, as needed ...
    return feed
