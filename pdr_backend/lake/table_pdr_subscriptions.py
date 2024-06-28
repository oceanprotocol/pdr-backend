#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from polars import Int64, Utf8, Float32

subscriptions_table_name = "pdr_subscriptions"

# RAW PREDICTOOR SUBSCRIPTIONS SCHEMA
subscriptions_schema = {
    "ID": Utf8,
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "tx_id": Utf8,
    "last_price_value": Float32,
    "timestamp": Int64,
    "user": Utf8,
}
