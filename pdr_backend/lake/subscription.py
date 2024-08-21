#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import OrderedDict
from typing import Callable, List

from enforce_typing import enforce_types
from polars import Float32, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class Subscription(LakeMapper):
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

    @staticmethod
    def get_fetch_function() -> Callable:
        # pylint: disable=import-outside-toplevel
        from pdr_backend.subgraph.subgraph_subscriptions import (
            fetch_filtered_subscriptions,
        )

        return fetch_filtered_subscriptions


# =========================================================================
# utilities for testing


@enforce_types
def mock_subscription(subscription_tuple: tuple) -> Subscription:
    (
        subscription_id,
        pair_str,
        timeframe_str,
        source,
        timestamp,
        tx_id,
        last_price_value,
        user,
    ) = subscription_tuple

    return Subscription(
        ID=subscription_id,
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
        """0x18f54cc21b7a2fdd011bea06bba7801b280e3151-
        0xe4599d8d1a02330fbc3a2a8fb4950f6d5a44d2e85fe750438246f535b47eda35-98""",
        "ETH/USDT",
        "5m",
        "binance",
        1698850800,  # Nov 01 2023 15:00 GMT/UTC
        "2.4979184013322233",
        98,
        "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
    ),
    (
        """0x18f54cc21b7a2fdd011bea06bba7801b280e3151-
        0xe4599d8d1a02330fbc3a2a8fb4950f6d5a44d2e85fe750438246f535b47eda35-98""",
        "ETH/USDT",
        "5m",
        "binance",
        1699870200,  # Nov 01 2023 15:00 GMT/UTC
        "4.11",
        99,
        "0x2433e002ed10b5d6a3d8d1e0c5d2083be9e37f1d",
    ),
    (
        """0x9c4a2406e5aa0f908d6e816e5318b9fc8a507e1f-
        0xe4599d8d1a02330fbc3a2a8fb4950f6d5a44d2e85fe750438246f535b47eda35-84""",
        "BTC/USDT",
        "5m",
        "kraken",
        1698937200,  # Nov 02 2023 15:00 GMT/UTC
        "2.4979184013322233",
        99,
        "0xabcdef0123456789abcdef0123456789abcdef01",
    ),
    (
        """0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-28""",
        "LTC/USDT",
        "1h",
        "kraken",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "2.4979184013322233",
        100,
        "0x123456789abcdef0123456789abcdef01234567",
    ),
    (
        """0x74a61f733bd9a2ce40d2e39738fe4912925c06dd-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-266""",
        "XRP/USDT",
        "5m",
        "binance",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "2.4979184013322233",
        101,
        "0xabcdef0123456789abcdef0123456789abcdef02",
    ),
    (
        """0x55c6c33514f80b51a1f1b63c8ba229feb132cedb-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-252""",
        "DOGE/USDT",
        "5m",
        "kraken",
        1699110000,  # Nov 04 2023 15:00 GMT/UTC
        "2.4979184013322233",
        102,
        "0xabcdef0123456789abcdef0123456789abcdef03",
    ),
    (
        """0x31fabe1fc9887af45b77c7d1e13c5133444ebfbd-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-238""",
        "ADA/USDT",
        "1h",
        "kraken",
        1699200000,  # Nov 05 2023 15:00 GMT/UTC
        "2.4979184013322233",
        103,
        "0xabcdef0123456789abcdef0123456789abcdef04",
    ),
    (
        """0x30f1c55e72fe105e4a1fbecdff3145fc14177695-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-224""",
        "DOT/USDT",
        "5m",
        "binance",
        1699200000,  # Nov 05 2023 15:00 GMT/UTC
        "2.4979184013322233",
        104,
        "0xabcdef0123456789abcdef0123456789abcdef05",
    ),
    (
        """0x2d8e2267779d27c2b3ed5408408ff15d9f3a3152-
        0x98cbb35e6180d2f8e7b50ee8cfbf9bb700a45dc56f0383fa448a782b80252457-210""",
        "LINK/USDT",
        "1h",
        "kraken",
        1699286400,  # Nov 06 2023 15:00 GMT/UTC
        "2.4979184013322233",
        105,
        "0xabcdef0123456789abcdef0123456789abcdef06",
    ),
]
