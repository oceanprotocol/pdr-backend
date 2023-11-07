import sys
import time
import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from enforce_typing import enforce_types

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.trader_config import TraderConfig
from pdr_backend.util.cache import Cache


# pylint: disable=too-many-instance-attributes
class TraderAgent:
    def __init__(
        self,
        trader_config: TraderConfig,
        _do_trade: Optional[Callable[[Feed, Tuple], Any]] = None,
        cache_dir=".cache",
    ):
        self.config = trader_config
        self._do_trade = _do_trade if _do_trade else self.do_trade

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
        self.load_cache()

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

        self.check_subscriptions_and_subscribe()

    def check_subscriptions_and_subscribe(self):
        for addr, feed in self.feeds.items():
            contract = PredictoorContract(self.config.web3_config, addr)
            if not contract.is_valid_subscription():
                print(f"Purchasing new subscription for feed: {feed}")
                contract.buy_and_start_subscription(None, True)
        time.sleep(1)

    def update_cache(self):
        for feed, epochs in self.prev_traded_epochs_per_feed.items():
            if epochs:
                last_epoch = epochs[-1]
                self.cache.save(f"trader_last_trade_{feed}", last_epoch)

    def load_cache(self):
        for feed in self.feeds:
            last_epoch = self.cache.load(f"trader_last_trade_{feed}")
            if last_epoch is not None:
                self.prev_traded_epochs_per_feed[feed].append(last_epoch)

    @enforce_types
    def run(self, testing: bool = False):
        while True:
            asyncio.run(self.take_step())
            if testing:
                break

    async def take_step(self):
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
        print("before:", time.time())
        tasks = [
            self._process_block_at_feed(addr, block["timestamp"]) for addr in self.feeds
        ]
        s_till_epoch_ends, log_list = zip(*await asyncio.gather(*tasks))

        for logs in log_list:
            for log in logs:
                print(log)

        print("after:", time.time())
        if -1 in s_till_epoch_ends:
            # -1 means subscription expired for one of the assets
            self.check_subscriptions_and_subscribe()
            return

        sleep_time = min(s_till_epoch_ends) - 1
        print(f"-- Soonest epoch is in {sleep_time} seconds, waiting... --")

        time.sleep(sleep_time)

    async def _process_block_at_feed(
        self, addr: str, timestamp: int, tries: int = 0
    ) -> Tuple[int, List[str]]:
        """
        @param:
            addr - contract address of the feed
            timestamp - timestamp/epoch to process
            [tries] - number of attempts made in case of an error, 0 by default
        @return:
            epoch_s_left - number of seconds left till the epoch end
            logs - list of strings of function logs
        """
        logs = []
        feed, predictoor_contract = self.feeds[addr], self.contracts[addr]
        s_per_epoch = feed.seconds_per_epoch
        epoch = int(timestamp / s_per_epoch)
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp
        logs.append(f"{'-'*40} Processing {feed} {'-'*40}\nEpoch {epoch}")
        logs.append("Seconds remaining in epoch: {epoch_s_left}")

        if (
            self.prev_traded_epochs_per_feed.get(addr)
            and epoch == self.prev_traded_epochs_per_feed[addr][-1]
        ):
            logs.append("      Done feed: already traded this epoch")
            return epoch_s_left, logs

        if epoch_s_left < self.config.trader_min_buffer:
            logs.append("      Done feed: not enough time left in epoch")
            return epoch_s_left, logs

        try:
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None, predictoor_contract.get_agg_predval, (epoch + 1) * s_per_epoch
            )
        except Exception as e:
            if tries < self.config.max_tries:
                logs.append(e.args[0]["message"])
                if (
                    len(e.args) > 0
                    and isinstance(e.args[0], dict)
                    and "message" in e.args[0]
                ):
                    revert_reason = e.args[0]["message"]
                    if revert_reason == "reverted: No subscription":
                        return (
                            -1,
                            logs,
                        )  # -1 means the subscription has expired for this pair
                logs.append("      Could not get aggpredval, trying again in a second")
                await asyncio.sleep(1)
                return await self._process_block_at_feed(addr, timestamp, tries + 1)
            logs.append(
                f"      Done feed: aggpredval not available, an error occured: {e}"
            )
            return epoch_s_left, logs

        await self._do_trade(feed, prediction)
        self.prev_traded_epochs_per_feed[addr].append(epoch)
        self.update_cache()
        return epoch_s_left, logs

    def get_pred_properties(
        self, pred_nom: float, pred_denom: float
    ) -> Dict[str, float]:
        """
        @description
            This function calculates the prediction direction and confidence.
        @returns
            A dictionary containing the following:
            - confidence: The confidence of the prediction.
            - direction: The direction of the prediction.
            - stake: The stake of the prediction.
        """
        confidence: float = pred_nom / pred_denom
        direction: float = 1 if confidence >= 0.5 else 0
        if confidence > 0.5:
            confidence -= 0.5
        else:
            confidence = 0.5 - confidence
        confidence = (confidence / 0.5) * 100

        return {
            "confidence": confidence,
            "dir": direction,
            "stake": pred_denom,
        }

    async def do_trade(self, feed: Feed, prediction: Tuple[float, float]):
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
        print(f"      {feed} has a new prediction: {pred_nom} / {pred_denom}.")

        pred_properties = self.get_pred_properties(pred_nom, pred_denom)
        print(f"      {feed} prediction properties: {pred_properties}.")
        # Trade here
        # ...
