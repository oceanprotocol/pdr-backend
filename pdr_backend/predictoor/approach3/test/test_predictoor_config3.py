import os

from enforce_typing import enforce_types

from pdr_backend.predictoor.approach3.predictoor_config3 import PredictoorConfig3

ADDR = "0xe8933f2950aec1080efad1ca160a6bb641ad245d"  # predictoor contract addr
PRIV_KEY = os.getenv("PRIVATE_KEY")


@enforce_types
def test_predictoor_config_basic(monkeypatch):
    _setenvs(monkeypatch)
    c = PredictoorConfig3()

    # values handled by PredictoorConfig3
    assert c.s_until_epoch_end == 60
    assert c.stake_amount == 30000

    # values handled by BaseConfig
    assert c.rpc_url == "http://foo"
    assert c.subgraph_url == "http://bar"
    assert c.private_key == PRIV_KEY

    assert c.pair_filters == ["BTC/USDT", "ETH/USDT"]
    assert c.timeframe_filter == ["5m", "15m"]
    assert c.source_filter == ["binance", "kraken"]
    assert c.owner_addresses == ["0x123", "0x124"]

    assert c.web3_config is not None


def _setenvs(monkeypatch):
    # envvars handled by PredictoorConfig3
    monkeypatch.setenv("SECONDS_TILL_EPOCH_END", "60")
    monkeypatch.setenv("STAKE_AMOUNT", "30000")

    # envvars handled by BaseConfig
    monkeypatch.setenv("RPC_URL", "http://foo")
    monkeypatch.setenv("SUBGRAPH_URL", "http://bar")
    monkeypatch.setenv("PRIVATE_KEY", PRIV_KEY)

    monkeypatch.setenv("PAIR_FILTER", "BTC/USDT,ETH/USDT")
    monkeypatch.setenv("TIMEFRAME_FILTER", "5m,15m")
    monkeypatch.setenv("SOURCE_FILTER", "binance,kraken")
    monkeypatch.setenv("OWNER_ADDRS", "0x123,0x124")
