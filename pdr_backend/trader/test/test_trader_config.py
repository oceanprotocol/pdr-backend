import os

from pdr_backend.trader.trader_config import TraderConfig


def test_trader_config(monkeypatch):
    monkeypatch.setenv("PAIR_FILTER", "BTC/USDT,ETH/USDT")
    monkeypatch.setenv("TIMEFRAME_FILTER", "5m,15m")
    monkeypatch.setenv("SOURCE_FILTER", "binance,kraken")
    monkeypatch.setenv("OWNER_ADDRS", "0x123,0x124")

    config = TraderConfig()

    # values handled by BaseConfig
    assert config.rpc_url == os.getenv("RPC_URL")
    assert config.subgraph_url == os.getenv("SUBGRAPH_URL")
    assert config.private_key == os.getenv("PRIVATE_KEY")

    assert config.pair_filters == ["BTC/USDT", "ETH/USDT"]
    assert config.timeframe_filter == ["5m", "15m"]
    assert config.source_filter == ["binance", "kraken"]
    assert config.owner_addresses == ["0x123", "0x124"]

    assert config.web3_config is not None
