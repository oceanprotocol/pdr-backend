import time
from typing import Dict, List, Tuple, Callable

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
        pending_slots = self.get_batch()

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
    def get_batch(self) -> List[Slot]:
        timestamp = self.config.web3_config.w3.eth.get_block("latest")["timestamp"]
        pending_slots = self.config.get_pending_slots(
            timestamp,
        )
        print(
            f"Found {len(pending_slots)} pending slots, processing {self.config.batch_size}"
        )
        pending_slots = pending_slots[: self.config.batch_size]
        return pending_slots

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

    def get_init_and_ts(self, slot: int, seconds_per_epoch: int) -> Tuple[int, int]:
        initial_ts = slot - seconds_per_epoch
        end_ts = slot
        return initial_ts, end_ts

    def get_and_submit_trueval(
        self,
        slot: Slot,
        predictoor_contract: PredictoorContract,
        seconds_per_epoch: int,
    ) -> dict:
        initial_ts, end_ts = self.get_init_and_ts(slot.slot_number, seconds_per_epoch)
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
        If the round should be canceled, the second value in the returned tuple is set to True.

    @arguments
        feed -- Feed -- The feed object containing pair details
        initial_timestamp -- int -- The starting timestamp.
        end_timestamp -- int -- The ending timestamp.

    @return
        Tuple[bool, bool] -- The trueval and a boolean indicating if the round should be canceled.
    """
    symbol = feed.pair
    symbol = symbol.replace("-", "/")
    symbol = symbol.upper()
    if initial_timestamp < 5000000000:
        initial_timestamp = int(initial_timestamp * 1000)
        end_timestamp = int(end_timestamp * 1000)

    exchange_class = getattr(ccxt, feed.source)
    exchange = exchange_class()
    price_data = exchange.fetch_ohlcv(
        symbol, feed.timeframe, since=initial_timestamp, limit=2
    )
    print(initial_timestamp, end_timestamp, symbol)
    print(price_data, feed.timeframe)
    if price_data[0][0] != initial_timestamp or price_data[1][0] != end_timestamp:
        raise Exception("Timestamp mismatch")

    if price_data[1][1] == price_data[0][1]:
        return (False, True)
    return (price_data[1][1] >= price_data[0][1], False)
