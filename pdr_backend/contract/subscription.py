from typing import List, Union

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
        event_index: int,
        user: str,
    ) -> None:
        self.ID = ID
        self.pair = pair
        self.timeframe = timeframe
        self.source = source
        self.timestamp = timestamp
        self.tx_id = tx_id
        self.event_index = event_index
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
        event_index=event_index,
        user=user,
    )


@enforce_types
def mock_first_subscriptions() -> List[Subscription]:
    return [
        mock_subscription(subscription_tuple) for subscription_tuple in _FIRST_SUBSCRIPTION_TUPS
    ]


@enforce_types
def mock_second_subscriptions() -> List[Subscription]:
    return [
        mock_subscription(subscription_tuple)
        for subscription_tuple in _SECOND_SUBSCRIPTION_TUPS
    ]

_FIRST_SUBSCRIPTION_TUPS = [
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809592-98",
        "ETH/USDT",
        "5m",
        "binance",
        1703030563,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809592",
        98,
        "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
    ),
        (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3152-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809593-99",
        "BTC/USDT",
        "5m",
        "kraken",
        1703030564,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809593",
        99,
        "0xabcdef0123456789abcdef0123456789abcdef01",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3153-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809594-100",
        "LTC/USDT",
        "1h",
        "kraken",
        1703030565,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809594",
        100,
        "0x123456789abcdef0123456789abcdef01234567",
    ),
]

_SECOND_SUBSCRIPTION_TUPS = [
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3154-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809595-101",
        "XRP/USDT",
        "5m",
        "binance",
        1703030566,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809595",
        101,
        "0xabcdef0123456789abcdef0123456789abcdef02",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3155-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809596-102",
        "DOGE/USDT",
        "5m",
        "kraken",
        1703030567,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809596",
        102,
        "0xabcdef0123456789abcdef0123456789abcdef03",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3156-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809597-103",
        "ADA/USDT",
        "1h",
        "kraken",
        1703030568,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809597",
        103,
        "0xabcdef0123456789abcdef0123456789abcdef04",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3157-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809598-104",
        "DOT/USDT",
        "5m",
        "binance",
        1703030569,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809598",
        104,
        "0xabcdef0123456789abcdef0123456789abcdef05",
    ),
    (
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3158-0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809599-105",
        "LINK/USDT",
        "1h",
        "kraken",
        1703030570,
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809599",
        105,
        "0xabcdef0123456789abcdef0123456789abcdef06",
    ),
]