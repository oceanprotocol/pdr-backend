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
        _get_trader: Optional[Callable[[Feed, Tuple], Any]] = None,
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

        # do work at new block
        for addr in self.feeds:
            self._process_block_at_feed(addr, block["timestamp"])

    def _process_block_at_feed(self, addr: str, timestamp: int):
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
            return None

        if epoch_s_left < self.config.trader_min_buffer:
            print("      Done feed: not enough time left in epoch")
            return None

        try:
            prediction = predictoor_contract.get_agg_predval((epoch + 1) * s_per_epoch)
        except Exception as e:
            print("      Done feed: aggpredval not available:", e)
            return None

        print(f"Got {prediction}.")

        self._get_trader(feed, prediction)
        self.prev_traded_epochs_per_feed[addr].append(epoch)


def get_trader(feed: Feed, prediction: Tuple[float, float]):
    """
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
