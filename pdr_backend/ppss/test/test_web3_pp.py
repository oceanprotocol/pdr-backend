import os
from unittest.mock import patch, Mock

from enforce_typing import enforce_types
from web3 import Web3

from pdr_backend.util.web3_config import Web3Config
from pdr_backend.ppss.web3_pp import Web3PP

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
    "address_file": "address.json 1",
    "rpc_url": "rpc url 1",
    "subgraph_url": "subgraph url 1",
    "stake_token": "0xStake1",
    "owner_addrs": "0xOwner1",
}
_D2 = {
    "address_file": "address.json 2",
    "rpc_url": "rpc url 2",
    "subgraph_url": "subgraph url 2",
    "stake_token": "0xStake2",
    "owner_addrs": "0xOwner2",
}
_D = {
    "network1": _D1,
    "network2": _D2,
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
    assert pp.owner_addrs == "0xOwner1"

    # network2
    pp2 = Web3PP("network2", _D)
    assert pp2.network == "network2"
    assert pp2.dn == _D2
    assert pp2.address_file == "address.json 2"


@enforce_types
def test_web3_pp__JIT_cached_properties(monkeypatch):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    web3_pp = Web3PP("network1", _D)

    # test web3_config
    assert web3_pp._web3_config is None

    c = web3_pp.web3_config  # calcs & caches web3_pp._web3_config
    assert isinstance(c, Web3Config)
    assert id(c) == id(web3_pp.web3_config)
    assert c.rpc_url == web3_pp.rpc_url
    assert c.private_key == PRIV_KEY
    assert isinstance(c.w3, Web3)

    # test derived properties
    assert web3_pp.private_key == PRIV_KEY
    assert isinstance(web3_pp.w3, Web3)
    assert id(web3_pp.w3) == id(c.w3)

    # test setter
    web3_pp.set_web3_config("foo")
    assert web3_pp.web3_config == "foo"

    # str
    assert "Web3PP=" in str(web3_pp)


@enforce_types
def test_web3_pp__get_pending_slots(monkeypatch):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    web3_pp = Web3PP("network1", _D)

    def _mock_get_pending_slots(*args, **kwargs):
        if len(args) >= 2:
            timestamp = args[1]
        else:
            timestamp = kwargs["timestamp"]
        return [f"1_{timestamp}", f"2_{timestamp}"]

    with patch("pdr_backend.ppss.web3_pp.get_pending_slots", _mock_get_pending_slots):
        slots = web3_pp.get_pending_slots(6789)
    assert slots == ["1_6789", "2_6789"]


@enforce_types
def test_web3_pp__get_feeds__get_contracts(monkeypatch):
    # test get_feeds() & get_contracts() at once, because one flows into other
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    web3_pp = Web3PP("network1", _D)

    # test get_feeds(). Uses results from get_feeds
    def _mock_query_feed_contracts(*args, **kwargs):  # pylint: disable=unused-argument
        feed_dicts = {ADDR: FEED_DICT}
        return feed_dicts

    with patch(
        "pdr_backend.ppss.web3_pp.query_feed_contracts",
        _mock_query_feed_contracts,
    ):
        feeds = web3_pp.get_feeds()

    feed_addrs = list(feeds.keys())
    assert feed_addrs == [ADDR]

    # test get_contracts(). Uses results from get_feeds
    def _mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.contract_address = ADDR
        return m

    with patch("pdr_backend.ppss.web3_pp.PredictoorContract", _mock_contract):
        contracts = web3_pp.get_contracts(feed_addrs)
    assert list(contracts.keys()) == feed_addrs
    assert contracts[ADDR].contract_address == ADDR
