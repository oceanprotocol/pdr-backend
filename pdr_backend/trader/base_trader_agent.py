import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed, print_feeds
from pdr_backend.util.cache import Cache
from pdr_backend.util.mathutil import sole_value


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
        contracts = ppss.web3_pp.get_contracts([feed.address])
        self.contract = sole_value(contracts)

        # set attribs to track block
        self.prev_block_timestamp: int = 0
        self.prev_block_number: int = 0

        self.prev_traded_epochs: List[int] = []

        self.cache = Cache(cache_dir=cache_dir)
        self.load_cache()

        self.check_subscriptions_and_subscribe()

    def check_subscriptions_and_subscribe(self):
        if not self.contract.is_valid_subscription():
            print(f"Purchase subscription for feed {self.feed}: begin")
            self.contract.buy_and_start_subscription(
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
        tasks = [self._process_block(block["timestamp"])]
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

    async def _process_block(
        self, timestamp: int, tries: int = 0
    ) -> Tuple[int, List[str]]:
        """
        @param:
            timestamp - timestamp/epoch to process
            [tries] - number of attempts made in case of an error, 0 by default
        @return:
            epoch_s_left - number of seconds left till the epoch end
            logs - list of strings of function logs
        """
        logs = []
        predictoor_contract = self.contract
        s_per_epoch = self.feed.seconds_per_epoch
        epoch = int(timestamp / s_per_epoch)
        epoch_s_left = epoch * s_per_epoch + s_per_epoch - timestamp
        logs.append(f"{'-'*40} Processing {self.feed} {'-'*40}\nEpoch {epoch}")
        logs.append(f"Seconds remaining in epoch: {epoch_s_left}")

        if self.prev_traded_epochs and epoch == self.prev_traded_epochs[-1]:
            logs.append("      Done feed: already traded this epoch")
            return epoch_s_left, logs

        if epoch_s_left < self.ppss.trader_ss.min_buffer:
            logs.append("      Done feed: not enough time left in epoch")
            return epoch_s_left, logs

        try:
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(
                None, predictoor_contract.get_agg_predval, (epoch + 1) * s_per_epoch
            )
        except Exception as e:
            if tries < self.ppss.trader_ss.max_tries:
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
                return await self._process_block(timestamp, tries + 1)
            logs.append(
                f"      Done feed: aggpredval not available, an error occured: {e}"
            )
            return epoch_s_left, logs

        await self._do_trade(self.feed, prediction)
        self.prev_traded_epochs.append(epoch)
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
        confidence = abs(confidence - 0.5)
        confidence = (confidence / 0.5) * 100

        return {
            "confidence": confidence,
            "dir": direction,
            "stake": pred_denom,
        }

    async def do_trade(self, feed: SubgraphFeed, prediction: Tuple[float, float]):
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
