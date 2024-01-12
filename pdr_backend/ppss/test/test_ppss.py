from copy import deepcopy
import os

from enforce_typing import enforce_types
import pytest

from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str, mock_feed_ppss, mock_ppss
from pdr_backend.ppss.web3_pp import del_network_override


@enforce_types
def test_ppss_from_file(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    yaml_filename = os.path.join(tmpdir, "ppss.yaml")
    with open(yaml_filename, "a") as f:
        f.write(yaml_str)

    _test_ppss(yaml_filename=yaml_filename, network="development")


@enforce_types
def test_ppss_from_str(tmpdir):
    yaml_str = fast_test_yaml_str(tmpdir)
    _test_ppss(yaml_str=yaml_str, network="development")


@enforce_types
def _test_ppss(yaml_filename=None, yaml_str=None, network=None):
    # construct
    ppss = PPSS(yaml_filename, yaml_str, network)

    # yaml properties - test lightly, since each *_pp and *_ss has its tests
    #  - so just do one test for each of this class's pp/ss attribute
    assert ppss.trader_ss.timeframe in ["5m", "1h"]
    assert isinstance(ppss.lake_ss.st_timestr, str)
    assert ppss.dfbuyer_ss.weekly_spending_limit >= 0
    assert ppss.predictoor_ss.aimodel_ss.approach == "LIN"
    assert ppss.payout_ss.batch_size >= 0
    assert 1 <= ppss.predictoor_ss.s_until_epoch_end <= 120
    assert isinstance(ppss.sim_ss.do_plot, bool)
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
def test_mock_feed_ppss(monkeypatch):
    del_network_override(monkeypatch)

    feed, ppss = mock_feed_ppss("5m", "binance", "BTC/USDT", "sapphire-mainnet")

    assert feed.timeframe == "5m"
    assert feed.source == "binance"
    assert feed.pair == "BTC/USDT"

    assert ppss.predictoor_ss.timeframe == "5m"
    assert str(ppss.predictoor_ss.feed) == "binance BTC/USDT c 5m"
    assert ppss.lake_ss.feeds_strs == ["binance BTC/USDT c 5m"]
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss_simple(monkeypatch):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"], "sapphire-mainnet")
    assert ppss.web3_pp.network == "sapphire-mainnet"


@enforce_types
def test_mock_ppss_default_network_development(monkeypatch):
    del_network_override(monkeypatch)
    ppss = mock_ppss(["binance BTC/USDT c 5m"])
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
def test_mock_ppss_onefeed1(feed_str, monkeypatch):
    """Thorough test that the 1-feed arg is used everywhere"""
    del_network_override(monkeypatch)

    ppss = mock_ppss([feed_str], "sapphire-mainnet")

    assert ppss.lake_ss.d["feeds"] == [feed_str]
    assert ppss.predictoor_ss.d["predict_feed"] == feed_str
    assert ppss.predictoor_ss.aimodel_ss.d["input_feeds"] == [feed_str]
    assert ppss.trader_ss.d["feed"] == feed_str
    assert ppss.trueval_ss.d["feeds"] == [feed_str]
    assert ppss.dfbuyer_ss.d["feeds"] == [feed_str]

    ppss.verify_feed_dependencies()


@enforce_types
def test_mock_ppss_manyfeed(monkeypatch):
    """Thorough test that the many-feed arg is used everywhere"""
    del_network_override(monkeypatch)

    feed_strs = ["binance BTC/USDT ETH/USDT c 5m", "kraken BTC/USDT c 5m"]
    feed_str = "binance BTC/USDT c 5m"  # must be the first in feed_strs
    ppss = mock_ppss(feed_strs, "sapphire-mainnet")

    assert ppss.lake_ss.d["feeds"] == feed_strs
    assert ppss.predictoor_ss.d["predict_feed"] == feed_str
    assert ppss.predictoor_ss.aimodel_ss.d["input_feeds"] == feed_strs
    assert ppss.trader_ss.d["feed"] == feed_str
    assert ppss.trueval_ss.d["feeds"] == feed_strs
    assert ppss.dfbuyer_ss.d["feeds"] == feed_strs

    ppss.verify_feed_dependencies()


@enforce_types
def test_verify_feed_dependencies(monkeypatch):
    del_network_override(monkeypatch)

    ppss = mock_ppss(
        ["binance BTC/USDT c 5m", "kraken ETH/USDT c 5m"],
        "sapphire-mainnet",
    )
    ppss.verify_feed_dependencies()

    # don't fail if aimodel needs more ohlcv feeds for same exchange/pair/time
    ppss2 = deepcopy(ppss)
    ppss2.predictoor_ss.aimodel_ss.d["input_feeds"] = ["binance BTC/USDT ohlcv 5m"]
    ppss2.verify_feed_dependencies()

    # fail check: is predictoor_ss.predict_feed in lake feeds?
    # - check for matching {exchange, pair, timeframe} but not {signal}
    assert "predict_feed" in ppss.predictoor_ss.d
    for wrong_feed in [
        "binance BTC/USDT o 5m",
        "binance ETH/USDT c 5m",
        "binance BTC/USDT c 1h",
        "kraken BTC/USDT c 5m",
    ]:
        ppss2 = deepcopy(ppss)
        ppss2.predictoor_ss.d["predict_feed"] = wrong_feed
        with pytest.raises(ValueError):
            ppss2.verify_feed_dependencies()

    # fail check: do all aimodel_ss input feeds conform to predict feed timeframe?
    ppss2 = deepcopy(ppss)
    ppss2.predictoor_ss.aimodel_ss.d["input_feeds"] = [
        "binance BTC/USDT c 5m",
        "binance BTC/USDT c 1h",
    ]  # 0th ok, 1st bad
    with pytest.raises(ValueError):
        ppss2.verify_feed_dependencies()

    # fail check: is each predictoor_ss.aimodel_ss.input_feeds in lake feeds?
    # - check for matching {exchange, pair, timeframe} but not {signal}
    for wrong_feed in [
        "kraken BTC/USDT c 5m",
        "binance ETH/USDT c 5m",
        "binance BTC/USDT c 1h",
    ]:
        ppss2 = deepcopy(ppss)
        ppss2.predictoor_ss.aimodel_ss.d["input_feeds"] = [wrong_feed]
        with pytest.raises(ValueError):
            ppss2.verify_feed_dependencies()

    # fail check: is predictoor_ss.predict_feed in aimodel_ss.input_feeds?
    # - check for matching {exchange, pair, timeframe AND signal}
    for wrong_feed in [
        "mexc BTC/USDT c 5m",
        "binance DOT/USDT c 5m",
        "binance BTC/USDT c 1h",
        "binance BTC/USDT o 5m",
    ]:
        ppss2 = deepcopy(ppss)
        ppss2.predictoor_ss.d["predict_feed"] = wrong_feed
        with pytest.raises(ValueError):
            ppss2.verify_feed_dependencies()
