from enforce_typing import enforce_types
import pytest
from typeguard import TypeCheckError

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset


# for "predict"
ARG_FEED_STR = "binance BTC/USDT o 1h"
ARG_FEED: ArgFeed = ArgFeed.from_str(ARG_FEED_STR)

# for "train_on"
ARG_FEEDS_STR = "binance BTC/USDT ETH/USDT o 1h"
ARG_FEEDS: ArgFeeds = ArgFeeds.from_str(ARG_FEEDS_STR)


@enforce_types
def test_feedset_main():
    feedset = PredictTrainFeedset(predict=ARG_FEED, train_on=ARG_FEEDS)

    assert feedset.predict == ARG_FEED
    assert feedset.train_on == ARG_FEEDS
    assert feedset.timeframe_ms == ARG_FEED.timeframe.ms

    assert feedset.to_dict() == {"predict": ARG_FEED_STR, "train_on": ARG_FEEDS_STR}

    assert (
        str(feedset)
        == "{'predict': 'binance BTC/USDT o 1h', 'train_on': 'binance BTC/USDT ETH/USDT o 1h'}"
    )


@enforce_types
def test_feedset_eq_same():
    feedset1 = PredictTrainFeedset(predict=ARG_FEED, train_on=ARG_FEEDS)
    feedset2 = PredictTrainFeedset(predict=ARG_FEED, train_on=ARG_FEEDS)
    assert feedset1 == feedset2


@enforce_types
def test_feedset_eq_diff():
    feedset1 = PredictTrainFeedset(predict=ARG_FEED, train_on=ARG_FEEDS)

    arg_feed2 = ArgFeed.from_str("kraken BTC/USDT o 1h")
    arg_feeds2 = ArgFeeds.from_str("kraken BTC/USDT ETH/USDT o 1h")

    # different "predict"
    feedset2a = PredictTrainFeedset(predict=arg_feed2, train_on=ARG_FEEDS)
    assert feedset1 != feedset2a

    # different "train_on"
    feedset2b = PredictTrainFeedset(predict=ARG_FEED, train_on=arg_feeds2)
    assert feedset1 != feedset2b


@enforce_types
def test_feedset_from_dict():
    # "train_on" as str
    d = {"predict": ARG_FEED_STR, "train_on": ARG_FEEDS_STR}
    feedset = PredictTrainFeedset.from_dict(d)
    assert feedset.predict == ARG_FEED
    assert feedset.train_on == ARG_FEEDS
    assert feedset.to_dict() == d

    # "train_on" as list
    d = {"predict": ARG_FEED_STR, "train_on": [ARG_FEEDS_STR]}
    feedset = PredictTrainFeedset.from_dict(d)
    assert feedset.predict == ARG_FEED
    assert feedset.train_on == ARG_FEEDS

    # "predict" value must be a str
    d = {"predict": ARG_FEED, "train_on": ARG_FEEDS_STR}
    with pytest.raises(TypeError):
        feedset = PredictTrainFeedset.from_dict(d)

    # "train_on" value must be a str
    d = {"predict": ARG_FEED_STR, "train_on": ARG_FEEDS}
    with pytest.raises(TypeCheckError):
        feedset = PredictTrainFeedset.from_dict(d)
