# pylint: disable=redefined-outer-name
import pytest

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_feeds import PredictFeed, parse_feed_obj


@pytest.fixture
def arg_feed_single():
    return ArgFeed("binance", "open", "BTC/USDT", "1h")


@pytest.fixture
def arg_feed_list() -> ArgFeeds:
    return ArgFeeds.from_str("binance BTC/USDT ETH/USDT o 1h")


def test_predict_feed_initialization(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)
    assert predict_feed.predict == arg_feed_single
    assert predict_feed.train_on == arg_feed_list


def test_predict_feed_from_feed_objs(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed.from_feed_objs(
        predict=arg_feed_single, train_on=arg_feed_list
    )
    assert predict_feed.predict == arg_feed_single
    assert predict_feed.train_on == arg_feed_list


def test_predict_feed_from_dict(arg_feed_single, arg_feed_list):
    dict_feed = {"predict": arg_feed_single, "train_on": arg_feed_list}
    predict_feed = PredictFeed.from_dict(dict_feed)
    assert predict_feed.predict == arg_feed_single
    assert predict_feed.train_on == arg_feed_list


def test_predict_feed_timeframe_ms(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)
    assert predict_feed.timeframe_ms == arg_feed_single.timeframe.ms


def test_predict_feed_predict_quote_str(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)
    assert predict_feed.predict_quote_str == "USDT"


def test_predict_feed_predict_base_str(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)
    assert predict_feed.predict_base_str == "BTC"


def test_predict_feed_predict_pair_str(arg_feed_single, arg_feed_list):
    predict_feed = PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)
    assert predict_feed.predict_pair_str == "BTC/USDT"


def test_parse_feed_obj():
    feed_str = "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    parsed = parse_feed_obj(feed_str)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"

    feed_list = ["binance BTC/USDT ETH/USDT o 1h", "kraken ADA/USDT c 5m"]

    parsed = parse_feed_obj(feed_list)

    assert type(parsed) == ArgFeeds
    assert str(parsed) == "binance BTC/USDT ETH/USDT o 1h, kraken ADA/USDT c 5m"
