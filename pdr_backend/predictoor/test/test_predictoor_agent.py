import os
import random
from typing import List
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach1.predictoor_config1 import PredictoorConfig1
from pdr_backend.predictoor.approach1.predictoor_agent1 import PredictoorAgent1
from pdr_backend.util.constants import S_PER_MIN, S_PER_DAY

PRIV_KEY = os.getenv("PRIVATE_KEY")

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"

SOURCE = "binance"
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


# mock PredictoorContract
@enforce_types
def toEpochStart(timestamp: int) -> int:
    return timestamp // S_PER_EPOCH * S_PER_EPOCH


# mock w3.eth.block_number, w3.eth.get_block()
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
class MockStack:
    def __init__(self, monkeypatch) -> None:
        self.mock_w3 = Mock()  # pylint: disable=not-callable
        self.mock_w3.eth = MockEth()
        self.mock_contract = MockContract(self.mock_w3)

        # mock query_feed_contracts()
        def mock_query_feed_contracts(
            *args, **kwargs
        ):  # pylint: disable=unused-argument
            feed_dicts = {ADDR: FEED_DICT}
            return feed_dicts

        def mock_contract_func(*args, **kwargs):  # pylint: disable=unused-argument
            return self.mock_contract

        monkeypatch.setattr(
            "pdr_backend.models.base_config.query_feed_contracts",
            mock_query_feed_contracts,
        )

        monkeypatch.setattr(
            "pdr_backend.models.base_config.PredictoorContract", mock_contract_func
        )

        # mock time.sleep()
        def advance_func(*args, **kwargs):  # pylint: disable=unused-argument
            do_advance_block = random.random() < 0.40
            if do_advance_block:
                self.mock_w3.eth.timestamp += random.randint(3, 12)
                self.mock_w3.eth.block_number += 1
                self.mock_w3.eth._timestamps_seen.append(self.mock_w3.eth.timestamp)

        monkeypatch.setattr("time.sleep", advance_func)

    def run_tests(self):
        # Initialize the Agent
        # Take steps with the Agent
        # Log final results for debugging / inspection
        pass


@enforce_types
def test_predictoor_base_agent(monkeypatch):
    _setenvs(monkeypatch)

    @enforce_types
    class MockBaseAgent(MockStack):
        def run_tests(self):
            # real work: initialize
            c = PredictoorConfig1()
            agent = PredictoorAgent1(c)

            # last bit of mocking
            agent.config.web3_config.w3 = self.mock_w3

            # real work: main iterations
            for _ in range(1000):
                agent.take_step()

            # log some final results for debubbing / inspection
            print("\n" + "=" * 80)
            print("Done iterations")
            print(
                f"init block_number = {INIT_BLOCK_NUMBER}"
                f", final = {self.mock_w3.eth.block_number}"
            )
            print()
            print(
                f"init timestamp = {INIT_TIMESTAMP}, final = {self.mock_w3.eth.timestamp}"
            )
            print(f"all timestamps seen = {self.mock_w3.eth._timestamps_seen}")
            print()
            print(
                "No unique prediction_slots = "
                f"{sorted(set(self.mock_contract._prediction_slots))}"
            )
            print(f"No prediction_slots = {self.mock_contract._prediction_slots}")

    agent = MockBaseAgent(monkeypatch)
    agent.run_tests()

    # relatively basic sanity tests
    assert agent.mock_contract._prediction_slots
    print(agent.mock_contract)
    print(agent.mock_w3.eth.timestamp)

    assert (agent.mock_w3.eth.timestamp + 2 * S_PER_EPOCH) >= max(
        agent.mock_contract._prediction_slots
    )


def _setenvs(monkeypatch):
    # envvars handled by PredictoorConfig1
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "60")
    monkeypatch.setenv("STAKE_AMOUNT", "30000")

    # envvars handled by BaseConfig
    monkeypatch.setenv("RPC_URL", "http://foo")
    monkeypatch.setenv("SUBGRAPH_URL", "http://bar")
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    monkeypatch.setenv("PAIR_FILTER", PAIR.replace("-", "/"))
    monkeypatch.setenv("TIMEFRAME_FILTER", TIMEFRAME)
    monkeypatch.setenv("SOURCE_FILTER", SOURCE)
    monkeypatch.setenv("OWNER_ADDRS", FEED_DICT["owner"])
