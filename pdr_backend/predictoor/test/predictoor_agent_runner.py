"""
This file exposes run_agent_test()
which is used by test_predictoor_agent{1,3}.py
"""
import os
import random
from typing import List
from unittest.mock import Mock

from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.data_ss import DataSS
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.util.constants import S_PER_DAY

PRIV_KEY = os.getenv("PRIVATE_KEY")
FEED_ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"
OWNER_ADDR = "0xowner"
INIT_TIMESTAMP = 107
INIT_BLOCK_NUMBER = 13


class MockQuery:
    def __init__(self, data_pp):
        feed_s = f"{data_pp.exchange_str}|{data_pp.pair_str}|{data_pp.timeframe}"
        feed_dict = {  # info inside a predictoor contract
            "name": f"Feed of {feed_s}",
            "address": FEED_ADDR,
            "symbol": f"FEED:{feed_s}",
            "seconds_per_epoch": data_pp.timeframe_s,
            "seconds_per_subscription": 1 * S_PER_DAY,
            "trueval_submit_timeout": 15,
            "owner": OWNER_ADDR,
            "pair": data_pp.pair_str,
            "timeframe": data_pp.timeframe,
            "source": data_pp.exchange_str,
        }
        self.feed_dict = feed_dict

    # mock query_feed_contracts()
    def mock_query_feed_contracts(
        self, *args, **kwargs
    ):  # pylint: disable=unused-argument
        feed_dicts = {self.feed_dict["address"]: self.feed_dict}
        return feed_dicts


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
class MockFeedContract:
    def __init__(self, w3, s_per_epoch: int):
        self._w3 = w3
        self.s_per_epoch = s_per_epoch
        self.contract_address: str = FEED_ADDR
        self._prediction_slots: List[int] = []

    def get_current_epoch(self) -> int:  # returns an epoch number
        return self.get_current_epoch_ts() // self.s_per_epoch

    def get_current_epoch_ts(self) -> int:  # returns a timestamp
        return self._w3.eth.timestamp // self.s_per_epoch * self.s_per_epoch

    def get_secondsPerEpoch(self) -> int:
        return self.s_per_epoch

    def submit_prediction(
        self, predval: bool, stake: float, timestamp: int, wait: bool = True
    ):  # pylint: disable=unused-argument
        assert stake <= 3
        if timestamp in self._prediction_slots:
            print(f"      (Replace prev pred at time slot {timestamp})")
        self._prediction_slots.append(timestamp)


@enforce_types
def run_agent_test(tmpdir, monkeypatch, predictoor_agent_class):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    ppss = _ppss(tmpdir)

    mock_query = MockQuery(ppss.data_pp)
    monkeypatch.setattr(
        "pdr_backend.ppss.web3_pp.query_feed_contracts",
        mock_query.mock_query_feed_contracts,
    )

    mock_w3 = Mock()  # pylint: disable=not-callable
    mock_w3.eth = MockEth()
    mock_feed_contract = MockFeedContract(mock_w3, ppss.data_pp.timeframe_s)

    # mock time.sleep()
    def advance_func(*args, **kwargs):  # pylint: disable=unused-argument
        do_advance_block = random.random() < 0.40
        if do_advance_block:
            mock_w3.eth.timestamp += random.randint(3, 12)
            mock_w3.eth.block_number += 1
            mock_w3.eth._timestamps_seen.append(mock_w3.eth.timestamp)

    def mock_contract_func(*args, **kwargs):  # pylint: disable=unused-argument
        return mock_feed_contract

    monkeypatch.setattr(
        "pdr_backend.ppss.web3_pp.PredictoorContract", mock_contract_func
    )
    monkeypatch.setattr("time.sleep", advance_func)

    # now we're done the mocking, time for the real work!!

    # real work: initialize
    agent = predictoor_agent_class(ppss)

    # last bit of mocking
    agent.ppss.web3_pp.web3_config.w3 = mock_w3

    # real work: main iterations
    for _ in range(100):
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
        "unique prediction_slots = "
        f"{sorted(set(mock_feed_contract._prediction_slots))}"
    )
    print(f"all prediction_slots = {mock_feed_contract._prediction_slots}")

    # relatively basic sanity tests
    assert mock_feed_contract._prediction_slots
    assert (mock_w3.eth.timestamp + 2 * ppss.data_pp.timeframe_s) >= max(
        mock_feed_contract._prediction_slots
    )


@enforce_types
def _ppss(tmpdir) -> PPSS:
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network="development")

    assert hasattr(ppss, "data_pp")
    ppss.data_pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["binanceus c BTC/USDT"],
            "sim_only": {"test_n": 10},
        }
    )
    assert hasattr(ppss, "data_ss")
    ppss.data_ss = DataSS(
        {
            "input_feeds": ["binanceus c BTC/USDT"],
            "parquet_dir": os.path.join("parquet_data"),
            "st_timestr": "2023-06-18",
            "fin_timestr": "2023-07-21",
            "max_n_train": 100,
            "autoregressive_n": 2,
        }
    )

    return ppss
