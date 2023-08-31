from pdr_backend.models.feed import Feed


def test_contract_data_initialization():
    feed = Feed(
        "Contract Name",
        "0x12345",
        "test",
        300,
        60,
        15,
        "0xowner",
        "BTC-ETH",
        "1h",
        "binance",
    )

    assert feed.name == "Contract Name"
    assert feed.address == "0x12345"
    assert feed.symbol == "test"
    assert feed.seconds_per_epoch == 300
    assert feed.seconds_per_subscription == 60
    assert feed.trueval_submit_timeout == 15
    assert feed.owner == "0xowner"
    assert feed.pair == "BTC-ETH"
    assert feed.timeframe == "1h"
    assert feed.source == "binance"
    assert feed.quote == "ETH"
    assert feed.base == "BTC"
