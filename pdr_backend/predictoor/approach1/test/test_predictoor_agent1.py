from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach1.predictoor_config1 import \
    PredictoorConfig1
from pdr_backend.predictoor.approach1.predictoor_agent1 import \
    PredictoorAgent1

PRIV_KEY = "0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"  # predictoor contract addr

FEED_DICT = {  # info inside a predictoor contract
    "name": "Contract Name",
    "address": ADDR,
    "symbol": "test",
    "seconds_per_epoch": 300,
    "seconds_per_subscription": 60,
    "trueval_submit_timeout": 15,
    "owner": "0xowner",
    "pair": "BTC-ETH",
    "timeframe": "1h",
    "source": "binance",
}


def test_predictoor_agent1(monkeypatch):
    _setenvs(monkeypatch)

    # mock query_feed_contracts()
    def mock_query_feed_contracts(*args, **kwargs):  # pylint: disable=unused-argument
        feed_dicts = {ADDR: FEED_DICT}
        return feed_dicts
    monkeypatch.setattr(
        "pdr_backend.models.base_config.query_feed_contracts",
        mock_query_feed_contracts,
    )

    # mock PredictoorContract
    def mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.contract_address = ADDR
        return m
    monkeypatch.setattr(
        "pdr_backend.models.base_config.PredictoorContract", mock_contract
    )
    
    # initialize
    c = PredictoorConfig1()
    agent = PredictoorAgent1(c)

    # mock w3.block_number, w3.get_block(), and time.sleep()
    class MockEth:
        def __init__(self):
            self.timestamp = 0
            self.block_number = 0
        def get_block(self, block_number, full_transactions):
            mock_block = {"timestamp": self.timestamp}
            return mock_block
        def advance_a_block(self):
            self.timestamp += 10
            self.block_number += 1
    mock_w3 = Mock()
    mock_w3.eth = MockEth()
    
    agent.config.web3_config.w3 = mock_w3
    monkeypatch.setattr(
        "time.sleep", mock_w3.advance_a_block
    )

    # mimic running
    for i in range(500):
        agent.take_step()


def _setenvs(monkeypatch):
    #envvars handled by PredictoorConfig1
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "60")
    monkeypatch.setenv("STAKE_AMOUNT", "30000")

    #envvars handled by BaseConfig
    monkeypatch.setenv("RPC_URL", "http://foo")
    monkeypatch.setenv("SUBGRAPH_URL", "http://bar")
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    
    monkeypatch.setenv("PAIR_FILTER", "BTC/USDT,ETH/USDT")
    monkeypatch.setenv("TIMEFRAME_FILTER", "5m,15m")
    monkeypatch.setenv("SOURCE_FILTER", "binance,kraken")
    monkeypatch.setenv("OWNER_ADDRS", "0x123,0x124")


