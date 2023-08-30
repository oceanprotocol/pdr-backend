from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.predictoor.predictoor_config import PredictoorConfig

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d" # predictoor contract addr
PRIV_KEY = "0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"

@enforce_types
class MyPredictoorConfig(PredictoorConfig):
    def __init__(self):
        super().__init__()
        self.get_prediction = "my prediction func"

@enforce_types
def test_predictoor_config_basic_with_filters(monkeypatch):
    _setenvs(monkeypatch, have_filters=True)
    c = MyPredictoorConfig()

    assert c.rpc_url == "http://foo"
    assert c.subgraph_url == "http://bar"
    assert c.private_key == PRIV_KEY
           
    assert c.s_until_epochs_end == 60
    assert c.stake_amount == 30000

    assert c.web3_config is not None
    assert c.get_prediction == "my prediction func"

    assert c.pair_filters == "BTC/USDT,ETH/USDT"
    assert c.timeframe_filter == "5m,15m"
    assert c.source_filter == "binance,kraken"
    assert c.owner_addresses == "0x123,0x124"

@enforce_types
def test_predictoor_config_basic_no_filters(monkeypatch):
    _setenvs(monkeypatch, have_filters=False)
    c = MyPredictoorConfig()
    assert c.pair_filters is None
    assert c.timeframe_filter is None
    assert c.source_filter is None
    assert c.owner_addresses is None

@enforce_types
def test_predictoor_config_feeds_contracts(monkeypatch):
    _setenvs(monkeypatch, have_filters=False)
    c = MyPredictoorConfig()

    with patch("pdr_backend.predictoor.predictoor_config.query_predictContracts", mock_query_predictContracts):
        feeds = c.get_feeds()        
    feed_addrs = list(feeds.keys())
    assert feed_addrs == [ADDR]
    
    with patch("pdr_backend.predictoor.predictoor_config.PredictoorContract", mock_contract):
        contracts = c.get_contracts(feed_addrs)
    assert list(contracts.keys()) == feed_addrs
    assert contracts[ADDR].contract_address == ADDR

def mock_query_predictContracts(*args, **kwargs):
    feeds_dict = {ADDR : "mock_contract"}
    return feeds_dict

def mock_contract(*args, **kwarg):
    m = Mock()
    m.contract_address = ADDR
    return m
    
def _setenvs(monkeypatch, have_filters:bool):
    monkeypatch.setenv("RPC_URL", "http://foo")
    monkeypatch.setenv("SUBGRAPH_URL", "http://bar")
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "60")
    monkeypatch.setenv("STAKE_AMOUNT", "30000")

    if have_filters:
        monkeypatch.setenv("PAIR_FILTER", "BTC/USDT,ETH/USDT")
        monkeypatch.setenv("TIMEFRAME_FILTER", "5m,15m")
        monkeypatch.setenv("SOURCE_FILTER", "binance,kraken")
        monkeypatch.setenv("OWNER_ADDRS", "0x123,0x124")
