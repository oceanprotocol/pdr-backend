from collections import OrderedDict
from typing import List

from enforce_typing import enforce_types
from polars import Float32, Int64, Utf8

from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class Subscription:
    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        pair: str,
        timeframe: str,
        source: str,
        timestamp: UnixTimeS,  # timestamp == subscription purchased timestamp
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

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,
                "pair": Utf8,
                "timeframe": Utf8,
                "source": Utf8,
                "tx_id": Utf8,
                "last_price_value": Float32,
                "timestamp": Int64,
                "user": Utf8,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "pdr_subscriptions"


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
        timestamp=UnixTimeS(timestamp),
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
        1698850800,  # Nov 01 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809592",
        "2.4979184013322233",
        98,
        "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
    ),
    (
        "BTC/USDT",
        "5m",
        "kraken",
        1698937200,  # Nov 02 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809593",
        "2.4979184013322233",
        99,
        "0xabcdef0123456789abcdef0123456789abcdef01",
    ),
    (
        "LTC/USDT",
        "1h",
        "kraken",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809594",
        "2.4979184013322233",
        100,
        "0x123456789abcdef0123456789abcdef01234567",
    ),
    (
        "XRP/USDT",
        "5m",
        "binance",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809595",
        "2.4979184013322233",
        101,
        "0xabcdef0123456789abcdef0123456789abcdef02",
    ),
    (
        "DOGE/USDT",
        "5m",
        "kraken",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809596",
        "2.4979184013322233",
        102,
        "0xabcdef0123456789abcdef0123456789abcdef03",
    ),
    (
        "ADA/USDT",
        "1h",
        "kraken",
        1699200000,  # Nov 05 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809597",
        "2.4979184013322233",
        103,
        "0xabcdef0123456789abcdef0123456789abcdef04",
    ),
    (
        "DOT/USDT",
        "5m",
        "binance",
        1699200000,  # Nov 05 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809598",
        "2.4979184013322233",
        104,
        "0xabcdef0123456789abcdef0123456789abcdef05",
    ),
    (
        "LINK/USDT",
        "1h",
        "kraken",
        1699286400,  # Nov 06 2023 15:00 GMT/UTC
        "0x01d3285e0e3b83a4c029142477c0573c3be5317ff68223703696093b27809599",
        "2.4979184013322233",
        105,
        "0xabcdef0123456789abcdef0123456789abcdef06",
    ),
]
