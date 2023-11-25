import os
from unittest.mock import patch, Mock

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig

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


@enforce_types
def test_base_config_with_filters(monkeypatch):
    _setenvs(monkeypatch, have_filters=True)
    c = BaseConfig()

    assert c.rpc_url == "http://foo"
    assert c.subgraph_url == "http://bar"
    assert c.private_key == PRIV_KEY

    assert c.pair_filters == ["BTC/USDT", "ETH/USDT"]
    assert c.timeframe_filter == ["5m", "15m"]
    assert c.source_filter == ["binance", "kraken"]
    assert c.owner_addresses == ["0x123", "0x124"]

    assert c.web3_config is not None


@enforce_types
def test_base_config_no_filters(monkeypatch):
    _setenvs(monkeypatch, have_filters=False)
    c = BaseConfig()
    assert c.pair_filters == []
    assert c.timeframe_filter == []
    assert c.source_filter == []
    assert c.owner_addresses == []


@enforce_types
def test_base_config_pending_slots(monkeypatch):
    _setenvs(monkeypatch, have_filters=False)
    c = BaseConfig()

    # test get_pending_slots()
    def _mock_get_pending_slots(*args):
        timestamp = args[1]
        return [f"1_{timestamp}", f"2_{timestamp}"]

    with patch(
        "pdr_backend.models.base_config.get_pending_slots", _mock_get_pending_slots
    ):
        slots = c.get_pending_slots(6789)
    assert slots == ["1_6789", "2_6789"]


@enforce_types
def test_base_config_feeds_contracts(monkeypatch):
    _setenvs(monkeypatch, have_filters=False)
    c = BaseConfig()

    # test get_feeds()
    def _mock_query_feed_contracts(*args, **kwargs):  # pylint: disable=unused-argument
        feed_dicts = {ADDR: FEED_DICT}
        return feed_dicts

    with patch(
        "pdr_backend.models.base_config.query_feed_contracts",
        _mock_query_feed_contracts,
    ):
        feeds = c.get_feeds()
    feed_addrs = list(feeds.keys())
    assert feed_addrs == [ADDR]

    # test get_contracts(). Uses results from get_feeds
    def _mock_contract(*args, **kwarg):  # pylint: disable=unused-argument
        m = Mock()
        m.contract_address = ADDR
        return m

    with patch("pdr_backend.models.base_config.PredictoorContract", _mock_contract):
        contracts = c.get_contracts(feed_addrs)
    assert list(contracts.keys()) == feed_addrs
    assert contracts[ADDR].contract_address == ADDR


@enforce_types
def _setenvs(monkeypatch, have_filters: bool):
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
