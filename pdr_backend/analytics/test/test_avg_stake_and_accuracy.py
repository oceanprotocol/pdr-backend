from pdr_backend.analytics.feed_avg_stake_and_accuracy import get_avg_stake_and_accuracy_for_feed
from pdr_backend.cli.arg_feed import ArgFeed


def test_get_avg_stake_and_accuracy():
    pairs = [
        "BTC/USDT", "ETH/USDT", "BNB/USDT", "XRP/USDT", 
        "ADA/USDT", "DOGE/USDT", "SOL/USDT", "LTC/USDT", 
        "TRX/USDT", "DOT/USDT"
    ]
    timeframes = ["5m", "1h"]

    for timeframe in timeframes:
        for pair in pairs:
            feed = ArgFeed("binance", "open", pair, timeframe)
            data = get_avg_stake_and_accuracy_for_feed(feed)
            assert data is not None, "Error, data is none"

            assert data[0] > 0
            assert data[1] > 0