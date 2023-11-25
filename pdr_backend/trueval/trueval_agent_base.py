import time
from abc import ABC
from typing import Dict, List, Tuple, Callable

import ccxt
from enforce_typing import enforce_types

from pdr_backend.models.slot import Slot
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.feed import Feed
from pdr_backend.trueval.trueval_config import TruevalConfig


@enforce_types
class TruevalAgentBase(ABC):
    def __init__(
        self,
        trueval_config: TruevalConfig,
        _get_trueval: Callable[[Feed, int, int], Tuple[bool, bool]],
    ):
        self.config = trueval_config
        self.get_trueval = _get_trueval
        self.contract_cache: Dict[str, tuple] = {}

    def run(self, testing: bool = False):
        while True:
            self.take_step()
            if testing:
                break

    def take_step(self):
        raise NotImplementedError("Take step is not implemented")

    def get_batch(self) -> List[Slot]:
        timestamp = self.config.web3_config.get_block("latest")["timestamp"]
        pending_slots = self.config.get_pending_slots(
            timestamp,
        )
        print(
            f"Found {len(pending_slots)} pending slots, processing {self.config.batch_size}"
        )
        pending_slots = pending_slots[: self.config.batch_size]
        return pending_slots

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

    def get_trueval_slot(self, slot: Slot):
        _, seconds_per_epoch = self.get_contract_info(slot.feed.address)
        init_ts, end_ts = self.get_init_and_ts(slot.slot_number, seconds_per_epoch)
        try:
            (trueval, cancel) = self.get_trueval(slot.feed, init_ts, end_ts)
            return trueval, cancel
        except Exception as e:
            if "Too many requests" in str(e):
                print("Too many requests, waiting for a minute")
                time.sleep(60)
                return self.get_trueval_slot(slot)

            # pylint: disable=line-too-long
            raise Exception(
                f"An error occured: {e}, while getting trueval for: {slot.feed.address} {slot.feed.pair} {slot.slot_number}"
            ) from e


@enforce_types
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

    # since we will get close price
    # we need to go back 1 candle
    initial_timestamp -= feed.seconds_per_epoch
    end_timestamp -= feed.seconds_per_epoch

    # convert seconds to ms
    initial_timestamp = int(initial_timestamp * 1000)
    end_timestamp = int(end_timestamp * 1000)

    exchange_class = getattr(ccxt, feed.source)
    exchange = exchange_class()
    price_data = exchange.fetch_ohlcv(
        symbol, feed.timeframe, since=initial_timestamp, limit=2
    )
    if price_data[0][0] != initial_timestamp or price_data[1][0] != end_timestamp:
        raise Exception("Timestamp mismatch")
    if price_data[1][4] == price_data[0][4]:
        return (False, True)
    return (price_data[1][4] >= price_data[0][4], False)
