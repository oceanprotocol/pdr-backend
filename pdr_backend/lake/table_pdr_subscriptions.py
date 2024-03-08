from polars import Int64, Utf8, Float32

subscriptions_table_name = "pdr_subscriptions"

# RAW PREDICTOOR SUBSCRIPTIONS SCHEMA
subscriptions_schema = {
    "ID": Utf8,  # id = {contract address}-{txid}-{eventIndex}
    "pair": Utf8,
    "timeframe": Utf8,
    "source": Utf8,
    "timestamp": Int64,
    "tx_id": Utf8,
    "last_price_value": Float32,
    "user": Utf8,
}
