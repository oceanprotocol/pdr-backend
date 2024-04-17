# pylint: disable=redefined-outer-name
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.parse_feed_obj import parse_feed_obj
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedset


@pytest.fixture
def arg_feed_single():
    return ArgFeed("binance", "open", "BTC/USDT", "1h")


@pytest.fixture
def arg_feed_list() -> ArgFeeds:
    return ArgFeeds.from_str("binance BTC/USDT ETH/USDT o 1h")


def test_predict_train_feedset_initialization(arg_feed_single, arg_feed_list):
    predict_train_feedset = PredictTrainFeedset(
        predict=arg_feed_single, train_on=arg_feed_list
    )
    assert predict_train_feedset.predict == arg_feed_single
    assert predict_train_feedset.train_on == arg_feed_list


def test_predict_train_feedset_from_feed_objs(arg_feed_single, arg_feed_list):
    predict_train_feedset = PredictTrainFeedset.from_feed_objs(
        predict=arg_feed_single, train_on=arg_feed_list
    )
    assert predict_train_feedset.predict == arg_feed_single
    assert predict_train_feedset.train_on == arg_feed_list


def test_predict_train_feedset_from_dict(arg_feed_single, arg_feed_list):
    dict_feed = {"predict": arg_feed_single, "train_on": arg_feed_list}
    predict_train_feedset = PredictTrainFeedset.from_dict(dict_feed)
    assert predict_train_feedset.predict == arg_feed_single
    assert predict_train_feedset.train_on == arg_feed_list


def test_predict_train_feedset_timeframe_ms(arg_feed_single, arg_feed_list):
    predict_train_feedset = PredictTrainFeedset(
        predict=arg_feed_single, train_on=arg_feed_list
    )
    assert predict_train_feedset.timeframe_ms == arg_feed_single.timeframe.ms


def test_predict_train_feedset_predict_pair_str(arg_feed_single, arg_feed_list):
    predict_train_feedset = PredictTrainFeedset(
        predict=arg_feed_single, train_on=arg_feed_list
    )
    assert predict_train_feedset.predict_pair_str == "BTC/USDT"


def test_parse_feed_obj():
    feed_str = "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    parsed = parse_feed_obj(feed_str)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    feed_list = ["binance BTC/USDT ETH/USDT o 1h", "kraken ADA/USDT c 5m"]

    parsed = parse_feed_obj(feed_list)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"
