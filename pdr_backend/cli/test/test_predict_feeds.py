import pytest
from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_feeds import PredictFeed, PredictFeeds


@pytest.fixture
def arg_feed_single():
    return ArgFeed("binance", "open", "BTC/USDT", "1h")

@pytest.fixture
def arg_feed_list() -> ArgFeeds:
    return ArgFeeds.from_str("binance BTC/USDT ETH/USDT o 1h")

@pytest.fixture
def arg_feed_predict_str():
    return "binance BTC/USDT o 1h"

@pytest.fixture
def arg_feed_train_on_str():
    return "binance BTC/USDT ETH/USDT o 1h"

@pytest.fixture
def predict_feed_fixture(arg_feed_single, arg_feed_list):
    return PredictFeed(predict=arg_feed_single, train_on=arg_feed_list)

def test_predict_feeds_initialization(predict_feed_fixture):
    feeds = [predict_feed_fixture]
    predict_feeds = PredictFeeds(feeds)
    assert len(predict_feeds) == 1
    assert predict_feeds[0] == predict_feed_fixture

def test_predict_feeds_from_array_valid_data(arg_feed_train_on_str, arg_feed_predict_str):
    array = [{"predict": arg_feed_predict_str, "train_on": arg_feed_train_on_str}]
    predict_feeds = PredictFeeds.from_array(array)
    assert len(predict_feeds) == 1
    assert predict_feeds[0].predict == ArgFeed.from_str(arg_feed_predict_str)
    assert predict_feeds[0].train_on == ArgFeeds.from_str(arg_feed_train_on_str)
    assert predict_feeds.min_epoch_seconds == 3600

def test_predict_feeds_from_array_missing_predict(arg_feed_train_on_str):
    with pytest.raises(ValueError) as excinfo:
        PredictFeeds.from_array([{"train_on": arg_feed_train_on_str}])
    assert "predict must be provided" in str(excinfo.value)

def test_predict_feeds_from_array_missing_train_on(arg_feed_predict_str):
    with pytest.raises(ValueError) as excinfo:
        PredictFeeds.from_array([{"predict": arg_feed_predict_str}])
    assert "train_on must be provided" in str(excinfo.value)

def test_predict_feeds_properties(predict_feed_fixture):
    predict_feeds = PredictFeeds([predict_feed_fixture, predict_feed_fixture])
    assert len(predict_feeds.feeds_str) == 2
    assert len(predict_feeds.feeds) == 2
    assert predict_feeds.min_epoch_seconds == 3600

def test_predict_feeds_to_list(predict_feed_fixture):
    predict_feeds = PredictFeeds([predict_feed_fixture])
    result = predict_feeds.to_list()
    assert isinstance(result, list)
    assert result[0]['predict'] == predict_feed_fixture.predict
