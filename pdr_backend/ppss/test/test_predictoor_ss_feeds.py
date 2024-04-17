from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict


@enforce_types
def test_predictoor_ss_feeds():
    d = predictoor_ss_test_dict()
    assert "feeds" in d
    d["feeds"] = [
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
    
    expected = [
        {
            "predict": ArgFeed.from_str("binance BTC/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeed.from_str("kraken BTC/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeed.from_str("binance ETH/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeed.from_str("binance ADA/USDT c 5m"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT DOT/USDT c 5m")
            + ArgFeeds.from_str("kraken BTC/USDT c 5m"),
        },
        {
            "predict": ArgFeed.from_str("binance BTC/USDT c 1h"),
            "train_on": ArgFeeds.from_str("binance BTC/USDT ETH/USDT c 5m"),
        },
    ]
    
    predictoor_ss = PredictoorSS(feed_dict)
    
    assert predictoor_ss.feeds.to_list() == expected
