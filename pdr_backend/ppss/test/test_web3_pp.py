import os
from unittest.mock import Mock, patch

import pytest
from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3
from pdr_backend.ppss.ppss import mock_feed_ppss

from pdr_backend.contract.predictoor_contract import mock_predictoor_contract
from pdr_backend.ppss.web3_pp import (
    Web3PP,
    inplace_mock_feedgetters,
    inplace_mock_get_contracts,
    inplace_mock_query_feed_contracts,
    mock_web3_pp,
)
from pdr_backend.subgraph.subgraph_feed import mock_feed
from pdr_backend.util.web3_config import Web3Config

PRIV_KEY = os.getenv("PRIVATE_KEY")

_D1 = {
    "address_file": "address.json 1",
    "rpc_url": "rpc url 1",
    "subgraph_url": "subgraph url 1",
    "owner_addrs": "0xOwner1",
}
_D2 = {
    "address_file": "address.json 2",
    "rpc_url": "rpc url 2",
    "subgraph_url": "subgraph url 2",
    "owner_addrs": "0xOwner2",
}
_D = {
    "network1": _D1,
    "network2": _D2,
}


def test_web3_config_pk():
    pp = Web3PP(_D, "network1")
    pk = os.getenv("PRIVATE_KEY_2")
    config = pp.web3_config_from_pk(pk)
    assert config.private_key == pk
    assert isinstance(config, Web3Config)


def test_web3_config_by_env():
    pp = Web3PP(_D, "network1")
    config = pp.web3_config_from_env("PRIVATE_KEY_2")
    assert config.private_key == os.getenv("PRIVATE_KEY_2")
    assert isinstance(config, Web3Config)

    # test cache
    cached = pp._web3_configs["PRIVATE_KEY_2"]
    assert id(cached) == id(config)


@enforce_types
def test_web3_pp__bad_network():
    with pytest.raises(ValueError):
        Web3PP(_D, "bad network")


@enforce_types
def test_web3_pp__yaml_dict():
    pp = Web3PP(_D, "network1")

    assert pp.network == "network1"
    assert pp.dn == _D1
    assert pp.address_file == "address.json 1"
    assert pp.rpc_url == "rpc url 1"
    assert pp.subgraph_url == "subgraph url 1"
    assert pp.owner_addrs == "0xOwner1"
    assert isinstance(pp.account, LocalAccount)

    # network2
    pp2 = Web3PP(_D, "network2")
    assert pp2.network == "network2"
    assert pp2.dn == _D2
    assert pp2.address_file == "address.json 2"


@enforce_types
def test_web3_pp__JIT_cached_properties(monkeypatch):
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    web3_pp = Web3PP(_D, "network1")

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
    web3_pp = Web3PP(_D, "network1")

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
def test_web3_pp__query_feed_contracts__get_contracts(monkeypatch):
    # test get_feeds() & get_contracts() at once, because one flows into other
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)
    web3_pp = Web3PP(_D, "network1")

    feed = mock_feed("5m", "binance", "BTC/USDT")

    # test get_feeds(). Uses results from get_feeds
    def _mock_subgraph_query_feed_contracts(
        *args, **kwargs
    ):  # pylint: disable=unused-argument
        return {feed.address: feed}

    with patch(
        "pdr_backend.ppss.web3_pp.query_feed_contracts",
        _mock_subgraph_query_feed_contracts,
    ):
        feeds = web3_pp.query_feed_contracts()

    assert list(feeds.keys()) == [feed.address]

    # test get_contracts(). Uses results from get_feeds
    def _mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.contract_address = feed.address
        return m

    with patch(
        "pdr_backend.contract.predictoor_contract.PredictoorContract",
        _mock_contract,
    ):
        contracts = web3_pp.get_contracts([feed.address])
    assert list(contracts.keys()) == [feed.address]
    assert contracts[feed.address].contract_address == feed.address


# =========================================================================
# test utilities for testing


@enforce_types
def test_mock_web3_pp():
    web3_pp = mock_web3_pp("development")
    assert isinstance(web3_pp, Web3PP)
    assert web3_pp.network == "development"

    web3_pp = mock_web3_pp("sapphire-mainnet")
    assert web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_inplace_mocks():
    web3_pp = mock_web3_pp("development")
    feed = mock_feed("5m", "binance", "BTC/USDT")

    # basic sanity test: can we call it without a fail?
    inplace_mock_feedgetters(web3_pp, feed)
    inplace_mock_query_feed_contracts(web3_pp, feed)

    c = mock_predictoor_contract(feed.address)
    inplace_mock_get_contracts(web3_pp, feed, c)


@enforce_types
def test_tx_gas_price__and__tx_call_params():
    web3_pp = mock_web3_pp("sapphire-testnet")
    eth_mock = Mock()
    eth_mock.gas_price = 12
    web3_pp.web3_config.w3.eth = eth_mock
    web3_pp.web3_config.owner = "0xowner"

    web3_pp.network = "sapphire-testnet"
    assert web3_pp.tx_gas_price() == 12
    assert web3_pp.tx_call_params() == {"from": "0xowner", "gasPrice": 12}

    web3_pp.network = "sapphire-mainnet"
    assert web3_pp.tx_gas_price() == 12

    web3_pp.network = "development"
    assert web3_pp.tx_gas_price() == 0
    assert web3_pp.tx_call_params() == {"from": "0xowner", "gasPrice": 0}

    web3_pp.network = "barge-pytest"
    assert web3_pp.tx_gas_price() == 0

    web3_pp.network = "foo"
    with pytest.raises(ValueError):
        web3_pp.tx_gas_price()
    with pytest.raises(ValueError):
        web3_pp.tx_call_params()


@enforce_types
def test_get_addresses():
    network = "development"
    _, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT")
    web3_pp = ppss.web3_pp
    assert web3_pp.network == network

    # Work 1: validate network can't be found
    with patch.object(web3_pp, "get_addresses", return_value=None):
        with pytest.raises(ValueError) as excinfo:
            web3_pp.OCEAN_address  # pylint: disable=pointless-statement

    assert 'Cannot find network "development"' in str(excinfo.value)

    return_value = {"Ocean": "0x1234567890123456789012345678901234567890"}
    with patch.object(web3_pp, "get_addresses", return_value=return_value):
        with pytest.raises(ValueError) as excinfo:
            web3_pp.get_address("ERCUnknown")

    assert 'Cannot find contract "ERCUnknown"' in str(excinfo.value)

    with patch.object(web3_pp, "get_addresses", return_value=return_value):
        assert web3_pp.OCEAN_address == "0x1234567890123456789012345678901234567890"
