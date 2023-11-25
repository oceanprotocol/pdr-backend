import os
import random
from typing import List
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3
from pdr_backend.predictoor.approach3.predictoor_agent3 import PredictoorAgent3
from pdr_backend.util.constants import S_PER_MIN, S_PER_DAY

PRIV_KEY = os.getenv("PRIVATE_KEY")

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"

SOURCE = "binanceus"
PAIR = "BTC-USDT"
TIMEFRAME, S_PER_EPOCH = "5m", 5 * S_PER_MIN  # must change both at once
SECONDS_TILL_EPOCH_END = 60  # how soon to start making predictions?
FEED_S = f"{PAIR}|{SOURCE}|{TIMEFRAME}"
S_PER_SUBSCRIPTION = 1 * S_PER_DAY
FEED_DICT = {  # info inside a predictoor contract
    "name": f"Feed of {FEED_S}",
    "address": ADDR,
    "symbol": f"FEED:{FEED_S}",
    "seconds_per_epoch": S_PER_EPOCH,
    "seconds_per_subscription": S_PER_SUBSCRIPTION,
    "trueval_submit_timeout": 15,
    "owner": "0xowner",
    "pair": PAIR,
    "timeframe": TIMEFRAME,
    "source": SOURCE,
}
INIT_TIMESTAMP = 107
INIT_BLOCK_NUMBER = 13


@enforce_types
def toEpochStart(timestamp: int) -> int:
    return timestamp // S_PER_EPOCH * S_PER_EPOCH


@enforce_types
class MockEth:
    def __init__(self):
        self.timestamp = INIT_TIMESTAMP
        self.block_number = INIT_BLOCK_NUMBER
        self._timestamps_seen: List[int] = [INIT_TIMESTAMP]

    def get_block(
        self, block_number: int, full_transactions: bool = False
    ):  # pylint: disable=unused-argument
        mock_block = {"timestamp": self.timestamp}
        return mock_block


@enforce_types
class MockContract:
    def __init__(self, w3):
        self._w3 = w3
        self.contract_address: str = ADDR
        self._prediction_slots: List[int] = []

    def get_current_epoch(self) -> int:  # returns an epoch number
        return self.get_current_epoch_ts() // S_PER_EPOCH

    def get_current_epoch_ts(self) -> int:  # returns a timestamp
        curEpoch_ts = toEpochStart(self._w3.eth.timestamp)
        return curEpoch_ts

    def get_secondsPerEpoch(self) -> int:
        return S_PER_EPOCH

    def submit_prediction(
        self, predval: bool, stake: float, timestamp: int, wait: bool = True
    ):  # pylint: disable=unused-argument
        assert stake <= 3
        if timestamp in self._prediction_slots:
            print(f"      (Replace prev pred at time slot {timestamp})")
        self._prediction_slots.append(timestamp)


@enforce_types
def test_predictoor_agent3(monkeypatch):
    _setenvs(monkeypatch)

    # mock query_feed_contracts()
    def mock_query_feed_contracts(*args, **kwargs):  # pylint: disable=unused-argument
        feed_dicts = {ADDR: FEED_DICT}
        return feed_dicts

    monkeypatch.setattr(
        "pdr_backend.models.base_config.query_feed_contracts",
        mock_query_feed_contracts,
    )

    # mock w3.eth.block_number, w3.eth.get_block()

    mock_w3 = Mock()  # pylint: disable=not-callable
    mock_w3.eth = MockEth()

    # mock PredictoorContract
    mock_contract = MockContract(mock_w3)

    def mock_contract_func(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_contract

    monkeypatch.setattr(
        "pdr_backend.models.base_config.PredictoorContract", mock_contract_func
    )

    # mock time.sleep()
    def advance_func(*args, **kwargs):  # pylint: disable=unused-argument
        do_advance_block = random.random() < 0.40
        if do_advance_block:
            mock_w3.eth.timestamp += random.randint(3, 12)
            mock_w3.eth.block_number += 1
            mock_w3.eth._timestamps_seen.append(mock_w3.eth.timestamp)

    monkeypatch.setattr("time.sleep", advance_func)

    # now we're done the mocking, time for the real work!!

    # real work: initialize
    c = PredictoorConfig3()
    agent = PredictoorAgent3(c)

    # last bit of mocking
    agent.config.web3_config.w3 = mock_w3

    # real work: main iterations
    for _ in range(1000):
        agent.take_step()

    # log some final results for debubbing / inspection
    print("\n" + "=" * 80)
    print("Done iterations")
    print(
        f"init block_number = {INIT_BLOCK_NUMBER}"
        f", final = {mock_w3.eth.block_number}"
    )
    print()
    print(f"init timestamp = {INIT_TIMESTAMP}, final = {mock_w3.eth.timestamp}")
    print(f"all timestamps seen = {mock_w3.eth._timestamps_seen}")
    print()
    print(
        "unique prediction_slots = " f"{sorted(set(mock_contract._prediction_slots))}"
    )
    print(f"all prediction_slots = {mock_contract._prediction_slots}")

    # relatively basic sanity tests
    assert mock_contract._prediction_slots
    assert (mock_w3.eth.timestamp + 2 * S_PER_EPOCH) >= max(
        mock_contract._prediction_slots
    )


def _setenvs(monkeypatch):
    # envvars handled by PredictoorConfig3
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "60")
    monkeypatch.setenv("STAKE_AMOUNT", "1")

    # envvars handled by BaseConfig
    monkeypatch.setenv("RPC_URL", "http://foo")
    monkeypatch.setenv("SUBGRAPH_URL", "http://bar")
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    monkeypatch.setenv("PAIR_FILTER", PAIR.replace("-", "/"))
    monkeypatch.setenv("TIMEFRAME_FILTER", TIMEFRAME)
    monkeypatch.setenv("SOURCE_FILTER", SOURCE)
    monkeypatch.setenv("OWNER_ADDRS", FEED_DICT["owner"])
