import os
import pytest
from pdr_backend.utils import env


def test_get_rpc_url_or_exit(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    with pytest.raises(SystemExit):
        env.get_rpc_url_or_exit()

    monkeypatch.setenv("RPC_URL", "http://test.url")
    assert env.get_rpc_url_or_exit() == "http://test.url"


def test_get_subgraph_or_exit(monkeypatch):
    monkeypatch.delenv("SUBGRAPH_URL", raising=False)
    with pytest.raises(SystemExit):
        env.get_subgraph_or_exit()

    monkeypatch.setenv("SUBGRAPH_URL", "http://subgraph.url")
    assert env.get_subgraph_or_exit() == "http://subgraph.url"


def test_get_private_key_or_exit(monkeypatch):
    monkeypatch.delenv("PRIVATE_KEY", raising=False)
    with pytest.raises(SystemExit):
        env.get_private_key_or_exit()

    monkeypatch.setenv("PRIVATE_KEY", "0xkey")
    assert env.get_private_key_or_exit() == "0xkey"


def test_get_pair_filter(monkeypatch):
    monkeypatch.delenv("PAIR_FILTER", raising=False)
    assert env.get_pair_filter() is None

    monkeypatch.setenv("PAIR_FILTER", "ETH/USDT")
    assert env.get_pair_filter() == "ETH/USDT"


def test_get_timeframe_filter(monkeypatch):
    monkeypatch.delenv("TIMEFRAME_FILTER", raising=False)
    assert env.get_timeframe_filter() is None

    monkeypatch.setenv("TIMEFRAME_FILTER", "1H")
    assert env.get_timeframe_filter() == "1H"


def test_get_source_filter(monkeypatch):
    monkeypatch.delenv("SOURCE_FILTER", raising=False)
    assert env.get_source_filter() is None

    monkeypatch.setenv("SOURCE_FILTER", "Uniswap")
    assert env.get_source_filter() == "Uniswap"


def test_get_owner_addresses(monkeypatch):
    monkeypatch.delenv("OWNER_ADDRS", raising=False)
    assert env.get_owner_addresses() is None

    monkeypatch.setenv("OWNER_ADDRS", "0x1234")
    assert env.get_owner_addresses() == "0x1234"
