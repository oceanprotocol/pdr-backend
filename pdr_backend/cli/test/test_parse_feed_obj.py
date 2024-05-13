from enforce_typing import enforce_types

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.parse_feed_obj import parse_feed_obj


@enforce_types
def test_parse_feed_obj():
    feed_str = "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    parsed = parse_feed_obj(feed_str)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    feed_list = ["binance BTC/USDT ETH/USDT o 1h", "kraken ADA/USDT c 5m"]

    parsed = parse_feed_obj(feed_list)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"
