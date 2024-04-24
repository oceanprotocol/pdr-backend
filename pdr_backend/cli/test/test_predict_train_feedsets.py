from enforce_typing import enforce_types
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_train_feedsets import (
    PredictTrainFeedset,
    PredictTrainFeedsets,
)

# for "predict"
ARG_FEED_STR = "binance BTC/USDT o 1h"
ARG_FEED: ArgFeed = ArgFeed.from_str(ARG_FEED_STR)

# for "train_on"
ARG_FEEDS_STR = "binance BTC/USDT ETH/USDT o 1h"
ARG_FEEDS: ArgFeeds = ArgFeeds.from_str(ARG_FEEDS_STR)

# ("predict", "train_on") set
FEEDSET_DICT = {"predict": ARG_FEED_STR, "train_on": ARG_FEEDS_STR}
FEEDSET = PredictTrainFeedset(predict=ARG_FEED, train_on=ARG_FEEDS)


@enforce_types
def test_feedsets_1_feedset():
    feedsets = PredictTrainFeedsets([FEEDSET])
    assert len(feedsets) == 1
    assert feedsets[0] == FEEDSET
    assert feedsets.to_list_of_dict() == [FEEDSET_DICT]
    assert feedsets.feed_strs == ["binance BTC/USDT o 1h", "binance ETH/USDT o 1h"]
    assert feedsets.feeds == [ARG_FEEDS[0], ARG_FEEDS[1]]
    assert feedsets.min_epoch_seconds == 3600

    assert feedsets == PredictTrainFeedsets([FEEDSET])
    assert (
        str(feedsets)
        == "[{'predict': 'binance BTC/USDT o 1h', 'train_on': 'binance BTC/USDT ETH/USDT o 1h'}]"
    )

    feedsets2 = PredictTrainFeedsets.from_list_of_dict([FEEDSET_DICT])
    assert feedsets2 == feedsets


@enforce_types
def test_feedsets_2_feedsets():
    feedsets = PredictTrainFeedsets([FEEDSET, FEEDSET])
    assert len(feedsets) == 2
    assert feedsets[0] == feedsets[1] == FEEDSET
    assert feedsets.to_list_of_dict() == [FEEDSET_DICT, FEEDSET_DICT]
    assert feedsets.feed_strs == ["binance BTC/USDT o 1h", "binance ETH/USDT o 1h"]
    assert feedsets.feeds == [ARG_FEEDS[0], ARG_FEEDS[1]]
    assert feedsets.min_epoch_seconds == 3600

    assert feedsets == PredictTrainFeedsets([FEEDSET, FEEDSET])

    feedsets2 = PredictTrainFeedsets.from_list_of_dict([FEEDSET_DICT, FEEDSET_DICT])
    assert feedsets2 == feedsets


@enforce_types
def test_feedsets_from_list_of_dict__bad_paths():
    # bad path: missing "predict" field
    with pytest.raises(ValueError):
        PredictTrainFeedsets.from_list_of_dict([{"train_on": ARG_FEEDS_STR}])

    # bad path: missing "train_on" field
    with pytest.raises(ValueError):
        PredictTrainFeedsets.from_list_of_dict([{"predict": ARG_FEED_STR}])


@enforce_types
def test_feedsets_from_list_of_dict__thorough():
    feedset_list = [
        {
            "predict": "binance BTC/USDT c 5m, kraken BTC/USDT c 5m",
            "train_on": [
                "binance BTC/USDT ETH/USDT DOT/USDT c 5m",
                "kraken BTC/USDT c 5m",
            ],
        },
        {
            "predict": "binance ETH/USDT ADA/USDT c 5m",
            "train_on": "binance BTC/USDT DOT/USDT c 5m, kraken BTC/USDT c 5m",
        },
    ]

    feedsets = PredictTrainFeedsets.from_list_of_dict(feedset_list)

    # - why 4 and not 2? Because each "predict" entry had _two_ feeds
    # - therefore 2 feeds for first dict, and 2 feeds for second dict
    # - 2 + 2 = 4 :)
    assert len(feedsets) == 4

    feedset_list2 = feedsets.to_list_of_dict()

    # when it outputs a list of dict, it doesn't compact back to 2 dicts. OK!
    target_feedset_list2 = [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT DOT/USDT ETH/USDT c 5m, kraken BTC/USDT c 5m",
        },
        {
            "predict": "kraken BTC/USDT c 5m",
            "train_on": "binance BTC/USDT DOT/USDT ETH/USDT c 5m, kraken BTC/USDT c 5m",
        },
        {
            "predict": "binance ETH/USDT c 5m",
            "train_on": "binance BTC/USDT DOT/USDT c 5m, kraken BTC/USDT c 5m",
        },
        {
            "predict": "binance ADA/USDT c 5m",
            "train_on": "binance BTC/USDT DOT/USDT c 5m, kraken BTC/USDT c 5m",
        },
    ]
    assert feedset_list2 == target_feedset_list2


@enforce_types
def test_feedsets__get_feedset():
    feedset_list = [
        {
            "predict": "binance BTC/USDT c 5m",
            "train_on": "binance BTC/USDT c 5m",
        },
        {
            "predict": "kraken BTC/USDT ETH/USDT c 5m",
            "train_on": "kraken BTC/USDT ETH/USDT DOT/USDT c 5m",
        },
    ]
    feedsets = PredictTrainFeedsets.from_list_of_dict(feedset_list)
    f0, f1, f2 = feedsets[0], feedsets[1], feedsets[2]

    assert f0.predict == ArgFeed("binance", "close", "BTC/USDT", "5m")
    assert f1.predict == ArgFeed("kraken", "close", "BTC/USDT", "5m")
    assert f2.predict == ArgFeed("kraken", "close", "ETH/USDT", "5m")

    assert feedsets.get_feedset("binance", "BTC/USDT", "5m") == f0
    assert feedsets.get_feedset("kraken", "BTC/USDT", "5m") == f1
    assert feedsets.get_feedset("kraken", "ETH/USDT", "5m") == f2

    assert feedsets.get_feedset("foo", "BTC/USDT", "5m") is None
    assert feedsets.get_feedset("binance", "foo", "5m") is None
    assert feedsets.get_feedset("binance", "BTC/USDT", "foo") is None

    with pytest.raises(TypeError):
        feedsets.get_feedset(1, "BTC/USDT", "5m")
    with pytest.raises(TypeError):
        feedsets.get_feedset("binance", 1, "5m")
    with pytest.raises(TypeError):
        feedsets.get_feedset("binance", "BTC/USDT", 1)
