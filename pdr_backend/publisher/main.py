from pdr_backend.publisher.publish import publish

publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="ETH",
    quote="USDT",
    source="kraken",
    timeframe="5m",
    trueval_submiter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)

publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="BTC",
    quote="TUSD",
    source="binance",
    timeframe="5m",
    trueval_submiter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)


publish(
    s_per_epoch=300,
    s_per_subscription=60 * 60 * 24,
    base="XRP",
    quote="USDT",
    source="binance",
    timeframe="5m",
    trueval_submiter_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    feeCollector_addr="0xe2DD09d719Da89e5a3D0F2549c7E24566e947260",
    rate=3,
    cut=0.2,
)
