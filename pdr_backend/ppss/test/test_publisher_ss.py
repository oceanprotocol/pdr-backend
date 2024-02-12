import pytest
from enforce_typing import enforce_types

from pdr_backend.ppss.publisher_ss import PublisherSS, mock_publisher_ss


@enforce_types
def test_publisher_ss():
    sapphire_feeds = [
        "binance BTC/USDT ETH/USDT BNB/USDT XRP/USDT"
        " ADA/USDT DOGE/USDT SOL/USDT LTC/USDT TRX/USDT DOT/USDT"
        " c 5m,1h"
    ]

    d = {
        "sapphire-mainnet": {
            "fee_collector_address": "0x1",
            "feeds": sapphire_feeds,
        },
        "sapphire-testnet": {
            "fee_collector_address": "0x2",
            "feeds": sapphire_feeds,
        },
    }

    ss1 = PublisherSS(d, "sapphire-mainnet")
    assert ss1.fee_collector_address == "0x1"

    ss2 = PublisherSS(d, "sapphire-testnet")
    assert ss2.fee_collector_address == "0x2"

    with pytest.raises(NotImplementedError):
        ss1.filter_feeds_from_candidates({})


@enforce_types
def test_mock_publisher_ss():
    publisher_ss = mock_publisher_ss("development")
    assert isinstance(publisher_ss, PublisherSS)
