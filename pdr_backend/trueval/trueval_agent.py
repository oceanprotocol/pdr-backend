import time
from typing import Dict, Tuple, Callable

import ccxt
from enforce_typing import enforce_types

from pdr_backend.models.slot import Slot
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.feed import Feed
from pdr_backend.trueval.trueval_config import TruevalConfig


class TruevalAgent:
    def __init__(
        self,
        trueval_config: TruevalConfig,
        _get_trueval: Callable[[Feed, int, int], Tuple[bool, bool]],
    ):
        self.config = trueval_config
        self.get_trueval = _get_trueval
        self.contract_cache: Dict[str, tuple] = {}

    @enforce_types
    def run(self, testing: bool = False):
        while True:
            self.take_step()
            if testing:
                break

    def take_step(self):
        timestamp = self.config.web3_config.w3.eth.get_block("latest")["timestamp"]
        pending_slots = self.config.get_pending_slots(
            self.config.subgraph_url,
            timestamp,
            self.config.owner_addresses,
            self.config.pair_filters,
            self.config.timeframe_filter,
            self.config.source_filter,
        )
        print(
            f"Found {len(pending_slots)} pending slots, processing {self.config.batch_size}"
        )
        pending_slots = pending_slots[: self.config.batch_size]

        if len(pending_slots) == 0:
            print(f"No pending slots, sleeping for {self.config.sleep_time} seconds...")
            time.sleep(self.config.sleep_time)
            return

        for slot in pending_slots:
            print("-" * 30)
            print(
                f"Processing slot {slot.slot_number} for contract {slot.feed.address}"
            )
            try:
                self.process_slot(slot)
            except Exception as e:
                print("An error occured", e)
        print(f"Done processing, sleeping for {self.config.sleep_time} seconds...")
        time.sleep(self.config.sleep_time)

    @enforce_types
    def process_slot(self, slot: Slot) -> dict:
        predictoor_contract, seconds_per_epoch = self.get_contract_info(
            slot.feed.address
        )
        return self.get_and_submit_trueval(slot, predictoor_contract, seconds_per_epoch)

    @enforce_types
    def get_contract_info(
        self, contract_address: str
    ) -> Tuple[PredictoorContract, int]:
        if contract_address in self.contract_cache:
            predictoor_contract, seconds_per_epoch = self.contract_cache[
                contract_address
            ]
        else:
            predictoor_contract = PredictoorContract(
                self.config.web3_config, contract_address
            )
            seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
            self.contract_cache[contract_address] = (
                predictoor_contract,
                seconds_per_epoch,
            )
        return (predictoor_contract, seconds_per_epoch)

    def get_and_submit_trueval(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
        seconds_per_epoch: int,
    ) -> dict:
        slot.slot_number = int(slot.slot_number)
        initial_ts = slot.slot_number - seconds_per_epoch
        end_ts = slot.slot_number

        (trueval, error) = self.get_trueval(slot.feed, initial_ts, end_ts)
        if error:
            raise Exception(
                f"Error getting trueval for {slot.feed.pair} and slot {slot.slot_number}"
            )

        # pylint: disable=line-too-long
        print(
            f"Contract:{predictoor_contract.contract_address} - Submitting trueval {trueval} and slot:{slot.slot_number}"
        )

        tx = predictoor_contract.submit_trueval(trueval, slot.slot_number, False, True)

        return tx


def get_trueval(
    feed: Feed, initial_timestamp: int, end_timestamp: int
) -> Tuple[bool, bool]:
    """
    @description
        Checks if the price has risen between two given timestamps.
        If an error occurs, the second value in the returned tuple is set to True.

    @arguments
        feed -- Feed -- The feed object containing pair details
        initial_timestamp -- int -- The starting timestamp.
        end_timestamp -- int -- The ending timestamp.

    @return
        Tuple[bool, bool] -- The trueval and a boolean indicating if an error occured.
    """
    symbol = feed.pair
    if feed.source == "binance" or feed.source == "kraken":
        symbol = symbol.replace("-", "/")
        symbol = symbol.upper()
    try:
        exchange_class = getattr(ccxt, feed.source)
        exchange_ccxt = exchange_class()
        price_initial = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=initial_timestamp, limit=1
        )
        price_end = exchange_ccxt.fetch_ohlcv(
            symbol, "1m", since=end_timestamp, limit=1
        )
        return (price_end[0][1] >= price_initial[0][1], False)
    except Exception as e:
        print(f"Error getting trueval for {symbol} {e}")
        return (False, True)
