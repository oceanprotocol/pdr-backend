import os
from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.models.web3_pp import Web3PP
from pdr_backend.util.web3_config import Web3Config

PRIV_KEY = os.getenv("PRIVATE_KEY")

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

_D1 = {
    "address_file" : "address.json 1",
    "rpc_url" : "rpc url 1",
    "subgraph_url" : "subgraph url 1",
    "stake_token" : "0xStake1",
    "owner_address" : "0xOwner1",
}
_D2 = {
    "address_file" : "address.json 2",
    "rpc_url" : "rpc url 2",
    "subgraph_url" : "subgraph url 2",
    "stake_token" : "0xStake2",
    "owner_address" : "0xOwner2",
}
_D = {
    "network1": _D1,
    "network2" : _D2, 
}

@enforce_types
def test_web3_pp__yaml_dict():    
    pp = Web3PP("network1", _D)

    assert pp.network == "network1"
    assert pp.dn == _D1
    assert pp.address_file == "address.json 1"
    assert pp.rpc_url == "rpc url 1"
    assert pp.subgraph_url == "subgraph url 1"
    assert pp.stake_token == "0xStake1"
    assert pp.owner_address == "0xOwner1"
    
    # network2
    pp2 = Web3PP("network2", _D)
    assert pp2.network == "network2"
    assert pp2.dn == _D2
    assert pp2.address_file == "address.json 2"

    
@enforce_types
def test_web3_pp__JIT_cached_properties(monkeypatch):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    pp = Web3PP("network1", _D)
    
    assert pp._private_key is None
    k = pp.private_key # calcs & caches pp._private_key 
    assert k == PRIV_KEY 
    assert pp._private_key is not None

    assert pp._web3_config is None
    w3 = pp.web3_config # calcs & caches pp._web3_config
    assert isinstance(w3, Web3Config)
    assert pp._web3_config is not None
    
    # str
    assert "Web3PP=" in str(pp)

    
@enforce_types
def test_web3_pp__get_pending_slots(monkeypatch):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    pp = Web3PP("network1", _D)

    def _mock_get_pending_slots(*args):
        timestamp = args[1]
        return [f"1_{timestamp}", f"2_{timestamp}"]
    
    with patch(
        "pdr_backend.models.web3_pp.get_pending_slots", _mock_get_pending_slots
    ):
        slots = pp.get_pending_slots(6789)
    assert slots == ["1_6789", "2_6789"]


@enforce_types
def test_web3_pp__get_feeds__get_contracts(monkeypatch):
    # test get_feeds() & get_contracts() at once, because one flows into other
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    pp = Web3PP("network1", _D)

    # test get_feeds(). Uses results from get_feeds
    def _mock_query_feed_contracts(*args, **kwargs):  # pylint: disable=unused-argument
        feed_dicts = {ADDR: FEED_DICT}
        return feed_dicts

    with patch(
        "pdr_backend.models.web3_pp.query_feed_contracts",
        _mock_query_feed_contracts,
    ):
        feeds = pp.get_feeds()
        
    feed_addrs = list(feeds.keys())
    assert feed_addrs == [ADDR]

    # test get_contracts(). Uses results from get_feeds
    def _mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.contract_address = ADDR
        return m

    with patch("pdr_backend.models.web3_pp.PredictoorContract", _mock_contract):
        contracts = pp.get_contracts(feed_addrs)
    assert list(contracts.keys()) == feed_addrs
    assert contracts[ADDR].contract_address == ADDR

