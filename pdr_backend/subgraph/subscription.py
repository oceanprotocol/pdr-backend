from typing import List

from enforce_typing import enforce_types


@enforce_types
class Subscription:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        pair: str,
        timeframe: str,
        source: str,
        timestamp: int,  # timestamp == subscription purchased timestamp
        tx_id: str,
        last_price_value: float,
        user: str,
    ) -> None:
        self.ID = ID
        self.pair = pair
        self.timeframe = timeframe
        self.source = source
        self.timestamp = timestamp
        self.tx_id = tx_id
        self.last_price_value = last_price_value
        self.user = user


# =========================================================================
# utilities for testing


@enforce_types
def mock_subscription(subscription_tuple: tuple) -> Subscription:
    (
        pair_str,
        timeframe_str,
        source,
        timestamp,
        tx_id,
        last_price_value,
        event_index,
        user,
    ) = subscription_tuple

    ID = f"{pair_str}-{tx_id}-{event_index}"
    return Subscription(
        ID=ID,
        pair=pair_str,
        timeframe=timeframe_str,
        source=source,
        timestamp=timestamp,
        tx_id=tx_id,
        last_price_value=float(last_price_value) * 1.201,
        user=user,
    )


@enforce_types
def mock_subscriptions() -> List[Subscription]:
    return [
        mock_subscription(subscription_tuple)
        for subscription_tuple in _SUBSCRIPTION_TUPS
    ]


_SUBSCRIPTION_TUPS = [
    (
        "ETH/USDT",
        "5m",
        "binance",
        1698850800,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809592",
        "2.4979184013322233",
        98,
        "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
    ),
    (
        "BTC/USDT",
        "5m",
        "kraken",
        1698937200,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809593",
        "2.4979184013322233",
        99,
        "0xabcdef0123456789abcdef0123456789abcdef01",
    ),
    (
        "LTC/USDT",
        "1h",
        "kraken",
        1699110000,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809594",
        "2.4979184013322233",
        100,
        "0x123456789abcdef0123456789abcdef01234567",
    ),
    (
        "XRP/USDT",
        "5m",
        "binance",
        1699110000,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809595",
        "2.4979184013322233",
        101,
        "0xabcdef0123456789abcdef0123456789abcdef02",
    ),
    (
        "DOGE/USDT",
        "5m",
        "kraken",
        1699110000,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809596",
        "2.4979184013322233",
        102,
        "0xabcdef0123456789abcdef0123456789abcdef03",
    ),
    (
        "ADA/USDT",
        "1h",
        "kraken",
        1699200000,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809597",
        "2.4979184013322233",
        103,
        "0xabcdef0123456789abcdef0123456789abcdef04",
    ),
    (
        "DOT/USDT",
        "5m",
        "binance",
        1699200000,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809598",
        "2.4979184013322233",
        104,
        "0xabcdef0123456789abcdef0123456789abcdef05",
    ),
    (
        "LINK/USDT",
        "1h",
        "kraken",
        1699286400,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809599",
        "2.4979184013322233",
        105,
        "0xabcdef0123456789abcdef0123456789abcdef06",
    ),
]
