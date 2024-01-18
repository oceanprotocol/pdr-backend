import asyncio
import time
from collections import namedtuple
from typing import Any, Callable, List, Optional, Tuple, Union

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed, print_feeds
from pdr_backend.util.cache import Cache
from pdr_backend.util.mathutil import sole_value

BasePrediction = namedtuple("BasePrediction", "pred_nom pred_denom")


class Prediction(BasePrediction):
    def __new__(cls, prediction: Tuple):
        return super().__new__(cls, *prediction)

    @property
    def confidence(self):
        return self.pred_nom / self.pred_denom

    @property
    def direction(self):
        return 1 if self.confidence >= 0.5 else 0

    @property
    def stake(self):
        return self.pred_denom

    @property
    def properties(self):
        return {
            "confidence": self.confidence,
            "direction": self.direction,
            "stake": self.pred_denom,
        }


# pylint: disable=too-many-instance-attributes
class BaseTraderAgent:
    def __init__(
        self,
        ppss: PPSS,
        _do_trade: Optional[Callable[[SubgraphFeed, Tuple], Any]] = None,
        cache_dir=".cache",
    ):
        # ppss
        self.ppss = ppss
        print("\n" + "-" * 80)
        print(self.ppss)

        # _do_trade
        self._do_trade = _do_trade or self.do_trade

        # set self.feeds
        cand_feeds = ppss.web3_pp.query_feed_contracts()
        print_feeds(cand_feeds, f"cand feeds, owner={ppss.web3_pp.owner_addrs}")

        feed = ppss.trader_ss.get_feed_from_candidates(cand_feeds)
        print_feeds({feed.address: feed}, "filtered feeds")
        if not feed:
            raise ValueError("No feeds found.")

        self.feed = feed
        feed_contracts = ppss.web3_pp.get_contracts([feed.address])
        self.feed_contract = sole_value(feed_contracts)

        # set attribs to track block
        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0

        self.prev_traded_epochs: List[int] = []

        self.cache = Cache(cache_dir=cache_dir)
        self.load_cache()

        self.check_subscriptions_and_subscribe()

    def check_subscriptions_and_subscribe(self):
        if not self.feed_contract.is_valid_subscription():
            print(f"Purchase subscription for feed {self.feed}: begin")
            self.feed_contract.buy_and_start_subscription(
                gasLimit=None,
                wait_for_receipt=True,
            )
            print(f"Purchase new subscription for feed {self.feed}: done")
        time.sleep(1)

    def update_cache(self):
        epochs = self.prev_traded_epochs
        if epochs:
            last_epoch = epochs[-1]
            self.cache.save(f"trader_last_trade_{self.feed.address}", last_epoch)

    def load_cache(self):
        last_epoch = self.cache.load(f"trader_last_trade_{self.feed.address}")
        if last_epoch is not None:
            self.prev_traded_epochs.append(last_epoch)

    def run(self, testing: bool = False):
        while True:
            asyncio.run(self.take_step())
            if testing:
                break

    async def take_step(self):
        web3_config = self.ppss.web3_pp.web3_config
        w3 = web3_config.w3

        # at new block number yet?
        block_number = w3.eth.block_number
        if block_number <= self.prev_block_number:
            time.sleep(1)
            return
        self.prev_block_number = block_number

        # is new block ready yet?
        block = web3_config.get_block(block_number, full_transactions=False)
        if not block:
            return

        self.prev_block_number = block_number
        self.prev_block_timestamp = block["timestamp"]
        print("before:", time.time())
        s_till_epoch_ends = await self._process_block(block["timestamp"])

        print("after:", time.time())
        if s_till_epoch_ends == -1:
            # -1 means subscription expired for one of the assets
            self.check_subscriptions_and_subscribe()
            return

        sleep_time = s_till_epoch_ends - 1
        print(f"-- epoch is in {sleep_time} seconds, waiting... --")

        time.sleep(sleep_time)

    async def _process_block(self, timestamp: int, tries: int = 0) -> int:
        """
        @param:
            timestamp - timestamp/epoch to process
            [tries] - number of attempts made in case of an error, 0 by default
        @return:
            epoch_s_left - number of seconds left till the epoch end
            logs - list of strings of function logs
        """
        feed_contract = self.feed_contract
        s_per_epoch = self.feed.seconds_per_epoch
        epoch = int(timestamp / s_per_epoch)
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp

        print(f"{'-'*40} Processing {self.feed} {'-'*40}\nEpoch {epoch}")
        print(f"Seconds remaining in epoch: {epoch_s_left}")

        if self.prev_traded_epochs and epoch == self.prev_traded_epochs[-1]:
            print("      Done feed: already traded this epoch")
            return epoch_s_left

        if epoch_s_left < self.ppss.trader_ss.min_buffer:
            print("      Done feed: not enough time left in epoch")
            return epoch_s_left

        try:
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None, feed_contract.get_agg_predval, (epoch + 1) * s_per_epoch
            )
        except Exception as e:
            if tries < self.ppss.trader_ss.max_tries:
                print(e.args[0]["message"])
                if (
                    len(e.args) > 0
                    and isinstance(e.args[0], dict)
                    and "message" in e.args[0]
                ):
                    revert_reason = e.args[0]["message"]
                    if revert_reason == "reverted: No subscription":
                        return -1
                print("      Could not get aggpredval, trying again in a second")
                await asyncio.sleep(1)
                return await self._process_block(timestamp, tries + 1)
            print(f"      Done feed: aggpredval not available, an error occured: {e}")
            return epoch_s_left

        await self._do_trade(self.feed, prediction)
        self.prev_traded_epochs.append(epoch)
        self.update_cache()

        return epoch_s_left

    async def do_trade(self, feed: SubgraphFeed, prediction: Union[Prediction, Tuple]):
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
        if not isinstance(prediction, Prediction):
            prediction = Prediction(prediction)

        print(
            f"      {feed} has a new prediction: {prediction.pred_nom} / {prediction.pred_denom}."
        )
        print(f"      {feed} prediction properties: {prediction.properties}.")
        # Trade here
        # ...
