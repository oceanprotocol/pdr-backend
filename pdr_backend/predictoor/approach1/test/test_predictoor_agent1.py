from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach1.predictoor_config1 import \
    PredictoorConfig1
from pdr_backend.predictoor.approach1.predictoor_agent1 import \
    PredictoorAgent1

PRIV_KEY = "0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"  # predictoor contract addr
S_PER_EPOCH = 100
S_PER_SUBSCRIPTION = 1000
FEED_DICT = {  # info inside a predictoor contract
    "name": "BTC-USDT feed",
    "address": ADDR,
    "symbol": "test",
    "seconds_per_epoch": S_PER_EPOCH,
    "seconds_per_subscription": S_PER_SUBSCRIPTION,
    "trueval_submit_timeout": 15,
    "owner": "0xowner",
    "pair": "BTC-ETH",
    "timeframe": "1h",
    "source": "binance",
}
INIT_EPOCH = 6

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
    class MockContract:
        def __init__(self):
            self.contract_address = ADDR
            self._current_epoch = INIT_EPOCH
            self._did_payout = False
        def get_current_epoch(self):
            return self._current_epoch
        def get_secondsPerEpoch(self):
            return S_PER_EPOCH
        def submit_prediction(self, predval, stake, timestamp, wait=True):
            pass
        def payout(self, slot, wait=False):
            self._did_payout = True
    mock_contract = MockContract()
    def mock_contract_func(*args, **kwargs):
        return mock_contract
    monkeypatch.setattr(
        "pdr_backend.models.base_config.PredictoorContract", mock_contract_func
    )

    # mock w3.eth.block_number, w3.eth.get_block()
    class MockEth:
        def __init__(self):
            self.timestamp = INIT_EPOCH * S_PER_EPOCH
            self.block_number = 0
        def get_block(self, block_number, full_transactions):
            mock_block = {"timestamp": self.timestamp}
            return mock_block
    mock_w3 = Mock()
    mock_w3.eth = MockEth()

    # mock time.sleep
    def advance_func(*args, **kwargs):
        assert S_PER_EPOCH == 100
        assert S_PER_SUBSCRIPTION == 1000
        mock_w3.eth.timestamp += 10
        mock_w3.eth.block_number += 1
        if mock_w3.eth.timestamp % 100 == 0:
            mock_contract._current_epoch += 1
        
    monkeypatch.setattr("time.sleep", advance_func)
    
    # initialize
    c = PredictoorConfig1()
    agent = PredictoorAgent1(c)

    # last bit of mocking
    agent.config.web3_config.w3 = mock_w3
    
    # main iterations
    for i in range(1000):
        agent.take_step()

    assert mock_contract._did_payout, "if False, make sure enough steps are run"


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


