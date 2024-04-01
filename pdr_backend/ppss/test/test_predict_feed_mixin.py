from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.predict_feed_mixin import PredictFeedMixin


def test_predict_feed_mixin():
    feed_dict = {
        "feeds": [
            {
                "predict": "binance BTC/USDT c 5m, kraken BTC/USDT c 5m",
                "train_on": [
                    "binance BTC/USDT ETH/USDT DOT/USDT c 5m",
                    "kraken BTC/USDT c 5m",
                ],
            },
            {
                "predict": "binance ETH/USDT ADA/USDT c 5m",
                "train_on": "binance BTC/USDT ETH/USDT DOT/USDT c 5m, kraken BTC/USDT c 5m",
            },
            {
                "predict": "binance BTC/USDT c 1h",
                "train_on": "binance BTC/USDT ETH/USDT c 5m",
            },
        ]
    }
    expected = [
        {
            "predict": ArgFeeds.from_str("binance BTC/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeeds.from_str("binance ETH/USDT ADA/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeeds.from_str("binance BTC/USDT c 1h"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT c 5m"),
        },
    ]
    parser = PredictFeedMixin(feed_dict)

    assert parser.feeds == expected
