import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.ppss.data_pp import DataPP, mock_data_pp
from pdr_backend.subgraph.subgraph_feed import mock_feed
from pdr_backend.util.mathutil import sole_value


@enforce_types
def test_data_pp_1feed():
    pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["kraken ETH/USDT h"],
            "sim_only": {"test_n": 2},
        }
    )

    # yaml properties
    assert isinstance(pp.timeframe, str)
    assert pp.predict_feeds_strs == ["kraken ETH/USDT h"]
    assert pp.test_n == 2

    # derivative properties
    assert isinstance(pp.timeframe_ms, int)  # test more below
    assert isinstance(pp.timeframe_m, int)  # ""
    assert pp.predict_feeds == [ArgFeed("kraken", "high", "ETH/USDT")]
    assert pp.pair_strs == ["ETH/USDT"]
    assert pp.exchange_strs == ["kraken"]
    assert pp.predict_feed == ArgFeed("kraken", "high", "ETH/USDT")
    assert pp.exchange_str == "kraken"
    assert pp.signal_str == "high"
    assert pp.pair_str == "ETH/USDT"
    assert pp.base_str == "ETH"
    assert pp.quote_str == "USDT"

    # str
    assert "DataPP" in str(pp)

    # setters
    pp.set_timeframe("1h")
    assert pp.timeframe == "1h"
    pp.set_predict_feeds(["binance BTC/DAI oh"])
    assert pp.predict_feeds_strs == ["binance BTC/DAI oh"]


@enforce_types
def test_data_pp_3feeds():
    pp = mock_data_pp("5m", ["kraken ETH/USDT h", "binance BTC/USDT oh"])

    # yaml properties
    assert pp.timeframe == "5m"
    assert pp.predict_feeds_strs == ["kraken ETH/USDT h", "binance BTC/USDT oh"]

    # derivative properties
    assert pp.predict_feeds == [
        ArgFeed("kraken", "high", "ETH/USDT"),
        ArgFeed("binance", "open", "BTC/USDT"),
        ArgFeed("binance", "high", "BTC/USDT"),
    ]
    assert pp.pair_strs == ["ETH/USDT", "BTC/USDT"]
    assert pp.exchange_strs == ["kraken", "binance"]
    with pytest.raises(ValueError):
        pp.predict_feed  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.exchange_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.signal_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.pair_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.base_str  # pylint: disable=pointless-statement
    with pytest.raises(ValueError):
        pp.quote_str  # pylint: disable=pointless-statement


@enforce_types
def test_pp_5m_vs_1h():
    pp = mock_data_pp("5m", ["binance ETH/USDT c"])
    assert pp.timeframe == "5m"
    assert pp.timeframe_ms == 5 * 60 * 1000
    assert pp.timeframe_s == 5 * 60
    assert pp.timeframe_m == 5

    # 1h
    pp = mock_data_pp("1h", ["binance ETH/USDT c"])
    assert pp.timeframe == "1h"
    assert pp.timeframe_ms == 60 * 60 * 1000
    assert pp.timeframe_s == 60 * 60
    assert pp.timeframe_m == 60


def _triplet(feed) -> tuple:
    return (feed.timeframe, feed.source, feed.pair)


@enforce_types
def test_filter_feeds_1allowed():
    # setup
    pp = mock_data_pp("5m", ["binance BTC/USDT c"])
    ok = [
        mock_feed("5m", "binance", "BTC/USDT"),
    ]
    not_ok = [
        mock_feed("1h", "binance", "BTC/USDT"),
        mock_feed("5m", "kraken", "BTC/USDT"),
        mock_feed("5m", "binance", "ETH/USDT"),
    ]
    cand_feeds = {f.address: f for f in ok + not_ok}
    ok_feed = ok[0]

    # work
    feeds = pp.filter_feeds(cand_feeds)

    # verify
    assert len(feeds) == 1
    assert list(feeds.keys())[0] == ok_feed.address

    feed = sole_value(feeds)
    assert _triplet(feed) == ("5m", "binance", "BTC/USDT")


@enforce_types
def test_filter_feeds_3allowed():
    # setup
    pp = mock_data_pp(
        "5m",
        ["binance BTC/USDT,ETH/USDT c", "kraken BTC/USDT c"],
    )
    ok = [
        mock_feed("5m", "binance", "BTC/USDT"),
        mock_feed("5m", "binance", "ETH/USDT"),
        mock_feed("5m", "kraken", "BTC/USDT"),
    ]
    not_ok = [
        mock_feed("5m", "binance", "XRP/USDT"),
        mock_feed("1h", "binance", "BTC/USDT"),
        mock_feed("5m", "kraken", "ETH/USDT"),
        mock_feed("1h", "kraken", "BTC/USDT"),
    ]
    cand_feeds = {f.address: f for f in ok + not_ok}
    ok_triplets = {_triplet(feed) for feed in ok}

    # work
    feeds = pp.filter_feeds(cand_feeds)

    # verify
    assert len(feeds) == 3
    triplets = {_triplet(feed) for feed in feeds.values()}
    assert triplets == ok_triplets


@enforce_types
def test_filter_feeds_joiner():
    _test_filter_feeds_joiner("/")
    _test_filter_feeds_joiner("-")


@enforce_types
def _test_filter_feeds_joiner(join_str):
    pp = mock_data_pp("5m", ["binance ETH/USDT c"])

    f1 = mock_feed("5m", "binance", f"BTC{join_str}USDT")
    f2 = mock_feed("5m", "binance", f"ETH{join_str}USDT")
    f3 = mock_feed("1h", "binance", f"BTC{join_str}USDT")
    cand_feeds = {f1.address: f1, f2.address: f2, f3.address: f3}

    final_feeds = pp.filter_feeds(cand_feeds)

    assert len(final_feeds) == 1
    assert list(final_feeds.keys()) == [f2.address]
    assert final_feeds[f2.address].name == f2.name
