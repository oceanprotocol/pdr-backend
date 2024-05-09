import os
from copy import deepcopy

import pytest

from enforce_typing import enforce_types

from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedsets
from pdr_backend.ppss.ppss import (
    fast_test_yaml_str,
    mock_feed_ppss,
    mock_ppss,
    PPSS,
)
from pdr_backend.ppss.predictoor_ss import feedset_test_list


@enforce_types
def test_ppss_main_from_file(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    yaml_filename = os.path.join(tmpdir, "ppss.yaml")
    with open(yaml_filename, "a") as f:
        f.write(yaml_str)

    _test_ppss(yaml_filename=yaml_filename, network="development")


@enforce_types
def test_ppss_main_from_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str, network="development")


@enforce_types
def _test_ppss(yaml_filename=None, yaml_str=None, network=None):
    # construct
    ppss = PPSS(yaml_filename, yaml_str, network)

    # yaml properties - test lightly, since each *_pp and *_ss has its tests
    #  - so just do one test for each of this class's pp/ss attribute
    assert ppss.trader_ss.timeframe_str in ["5m", "1h"]
    assert isinstance(ppss.lake_ss.st_timestr, str)
    assert ppss.dfbuyer_ss.weekly_spending_limit >= 0
    assert ppss.predictoor_ss.aimodel_ss.approach == "LinearLogistic"
    assert ppss.payout_ss.batch_size >= 0
    assert 1 <= ppss.predictoor_ss.s_until_epoch_end <= 120
    assert 0.0 <= ppss.trader_ss.fee_percent <= 0.99
    assert "USD" in ppss.trader_ss.buy_amt_str
    assert ppss.trueval_ss.batch_size >= 0
    assert isinstance(ppss.web3_pp.address_file, str)

    # str
    s = str(ppss)
    assert "lake_ss" in s
    assert "dfbuyer_ss" in s
    assert "payout_ss" in s
    assert "predictoor_ss" in s
    assert "sim_ss" in s
    assert "trader_ss" in s
    assert "trueval_ss" in s
    assert "web3_pp" in s


@enforce_types
def test_mock_feed_ppss():
    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT", "sapphire-mainnet")

    assert feed.timeframe == "5m"
    assert feed.source == "binance"
    assert feed.pair == "BTC/USDT"

    predict_feed0 = ppss.predictoor_ss.predict_train_feedsets[0].predict
    assert str(predict_feed0) == "binance BTC/USDT c 5m"
    assert ppss.lake_ss.feeds_strs == ["binance BTC/USDT c 5m"]
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss_simple():
    ppss = mock_ppss(feedset_test_list(), "sapphire-mainnet")
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss_default_network_development():
    ppss = mock_ppss(feedset_test_list())
    assert ppss.web3_pp.network == "development"


@enforce_types
@pytest.mark.parametrize(
    "feed_str",
    [
        "binance BTC/USDT c 5m",
        "binance ETH/USDT c 5m",
        "binance BTC/USDT o 5m",
        "binance BTC/USDT c 1h",
        "kraken ETH/USDT c 5m",
    ],
)
def test_mock_ppss_onefeed1(feed_str):
    """
    @description
      Thorough test that the 1-feed arg is used everywhere

    @arguments
      feed_str -- eg "binance BTC/USDT c 5m"
    """

    ppss = mock_ppss([{"predict": feed_str, "train_on": feed_str}], "sapphire-mainnet")

    assert ppss.lake_ss.d["feeds"] == [feed_str]
    assert ppss.predictoor_ss.d["predict_train_feedsets"] == [
        {"predict": feed_str, "train_on": feed_str}
    ]
    assert ppss.trader_ss.d["feed"] == feed_str
    assert ppss.trueval_ss.d["feeds"] == [feed_str]
    assert ppss.dfbuyer_ss.d["feeds"] == [feed_str]

    ppss.verify_feed_dependencies()


@enforce_types
def test_mock_ppss_manyfeed():
    """Thorough test that the many-feed arg is used everywhere"""

    feedset_list = [
        {
            "predict": "binance BTC/USDT ETH/USDT c 5m",
            "train_on": "binance BTC/USDT ETH/USDT c 5m",
        },
        {
            "predict": "kraken BTC/USDT c 5m",
            "train_on": "kraken BTC/USDT c 5m",
        },
    ]
    ppss = mock_ppss(feedset_list, "sapphire-mainnet")

    feedsets = PredictTrainFeedsets.from_list_of_dict(feedset_list)
    assert ppss.lake_ss.d["feeds"] == feedsets.feed_strs
    assert ppss.predictoor_ss.d["predict_train_feedsets"] == feedset_list
    assert ppss.trader_ss.d["feed"] == feedsets.feed_strs[0]
    assert ppss.trueval_ss.d["feeds"] == feedsets.feed_strs
    assert ppss.dfbuyer_ss.d["feeds"] == feedsets.feed_strs

    ppss.verify_feed_dependencies()


@enforce_types
def test_verify_feed_dependencies():
    # create ppss
    ppss = mock_ppss(
        feedset_test_list(),
        "sapphire-mainnet",
    )
    assert "predict_train_feedsets" in ppss.predictoor_ss.d

    # baseline should pass
    ppss.verify_feed_dependencies()

    # fail check: does lake feeds hold each predict feed? Each train feed?
    # - check for matching {exchange, pair, timeframe} but not {signal}
    good_feed = "binance BTC/USDT c 5m"
    for wrong_feed in [
        "dydx BTC/USDT c 5m",  # bad exchange
        "binance DOT/USDT c 5m",  # bad pair
        "binance BTC/USDT c 1h",  # bad timeframe
    ]:
        # test lake <> predict feed
        ppss2 = deepcopy(ppss)
        ppss2.predictoor_ss.d["predict_train_feedsets"] = [
            {"predict": wrong_feed, "train_on": good_feed}
        ]
        with pytest.raises(ValueError):
            ppss2.verify_feed_dependencies()

        # test lake <> train feed
        ppss2 = deepcopy(ppss)
        ppss2.predictoor_ss.d["predict_train_feedsets"] = [
            {"predict": good_feed, "train_on": wrong_feed}
        ]
        with pytest.raises(ValueError):
            ppss2.verify_feed_dependencies()

    # fail check: do all feeds in predict/train sets have identical timeframe?
    ppss2 = deepcopy(ppss)
    ppss2.predictoor_ss.d["predict_train_feedsets"] = [
        {"predict": "binance BTC/USDT c 5m", "train_on": "binance BTC/USDT c 1h"}
    ]
    with pytest.raises(ValueError):
        ppss2.verify_feed_dependencies()

    # fail check: is the predict feed in the corr. train feeds?
    ppss2 = deepcopy(ppss)
    ppss2.predictoor_ss.d["predict_train_feedsets"] = [
        {"predict": "binance BTC/USDT c 5m", "train_on": "binance ETH/USDT c 5m"}
    ]
    with pytest.raises(ValueError):
        ppss2.verify_feed_dependencies()
