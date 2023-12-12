import time
from abc import ABC
from typing import Dict, List, Tuple, Callable

import ccxt
from enforce_typing import enforce_types

from pdr_backend.data_eng.fetch_ohlcv import safe_fetch_ohlcv
from pdr_backend.models.slot import Slot
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.feed import Feed
from pdr_backend.ppss.ppss import PPSS


@enforce_types
class TruevalAgentBase(ABC):
    def __init__(
        self,
        ppss: PPSS,
        _get_trueval: Callable[[Feed, int, int], Tuple[bool, bool]],
    ):
        self.ppss = ppss
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
        timestamp = self.ppss.web3_pp.web3_config.get_block("latest")["timestamp"]
        pending_slots = self.ppss.web3_pp.get_pending_slots(
            timestamp,
        )
        print(
            f"Found {len(pending_slots)} pending slots"
            f", processing {self.ppss.trueval_ss.batch_size}"
        )
        pending_slots = pending_slots[: self.ppss.trueval_ss.batch_size]
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
                self.ppss.web3_pp, contract_address
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
    feed: Feed, init_timestamp: int, end_timestamp: int
) -> Tuple[bool, bool]:
    """
    @description
        Checks if the price has risen between two given timestamps.
        If the round should be canceled, the second value in the returned tuple is set to True.

    @arguments
        feed -- Feed -- The feed object containing pair details
        init_timestamp -- int -- The starting timestamp.
        end_timestamp -- int -- The ending timestamp.

    @return
        trueval -- did price rise y/n?
        cancel_round -- should we cancel the round y/n?
    """
    symbol = feed.pair
    symbol = symbol.replace("-", "/")
    symbol = symbol.upper()

    # since we will get close price
    # we need to go back 1 candle
    init_timestamp -= feed.seconds_per_epoch
    end_timestamp -= feed.seconds_per_epoch

    # convert seconds to ms
    init_timestamp = int(init_timestamp * 1000)
    end_timestamp = int(end_timestamp * 1000)

    exchange_class = getattr(ccxt, feed.source)
    exchange = exchange_class()
    tohlcvs = safe_fetch_ohlcv(
        exchange, symbol, feed.timeframe, since=init_timestamp, limit=2
    )
    assert len(tohlcvs) == 2, f"expected exactly 2 tochlv tuples. {tohlcvs}"
    init_tohlcv, end_tohlcv = tohlcvs[0], tohlcvs[1]

    assert init_tohlcv[0] == init_timestamp, (init_tohlcv[0], init_timestamp)
    assert end_tohlcv[0] == end_timestamp, (end_tohlcv[0], end_timestamp)

    init_c, end_c = init_tohlcv[4], end_tohlcv[4]  # c = closing price
    if end_c == init_c:
        trueval = False
        cancel_round = True
        return trueval, cancel_round

    trueval = end_c > init_c
    cancel_round = False
    return trueval, cancel_round
