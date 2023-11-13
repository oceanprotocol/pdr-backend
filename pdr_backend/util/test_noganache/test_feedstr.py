from enforce_typing import enforce_types

from pdr_backend.util.feedstr import (
    pair_str,
    unpack_pair_str,
    unpack_pairs_str,
    unpack_feed_str,
    unpack_feeds_str,
)


@enforce_types
def test_pair_str():
    assert pair_str("BTC", "USDT") == "BTC/USDT"

    
@enforce_types
def test_unpack_pair_str():
    assert unpack_pair_str("BTC/USDT") == ("BTC","USDT")
    assert unpack_pair_str("BTC-USDT") == ("BTC","USDT")

    
@enforce_types
def test_unpack_pairs_str():
    pairs_list = unpack_pairs_str("ADA/USDT BTC/USDT")
    assert pairs_list == ["ADA/USDT","BTC/USDT"]
    
    pairs_list = unpack_pairs_str("ADA/USDT,BTC/USDT")
    assert pairs_list == ["ADA/USDT","BTC/USDT"]

    pairs_list = unpack_pairs_str("ADA/USDT, BTC/USDT")
    assert pairs_list == ["ADA/USDT","BTC/USDT"]

    pairs_list = unpack_pairs_str("ADA/USDT BTC/USDT,ETH/USDC, DOT/DAI")
    assert pairs_list == ["ADA/USDT", "BTC/USDT", "ETH/USDC", "DOT/DAI"]


@enforce_types
def test_unpack_feed_str():
    exchange_id, signal, pair = unpack_feed_str("binance c BTC/USDT")
    assert exchange_id == "binance"
    assert signal == "close"
    assert pair == "BTC/USDT"


@enforce_types
def test_unpack_feeds_str():
    #basic
    tup = unpack_feeds_str("binance oc ADA/USDT,BTC/USDT")
    (exchange_id, signals, pairs) = tup
    assert exchange_id == "binance"
    assert signals == ["open", "close"]
    assert pairs ==  ["ADA/USDT", "BTC/USDT"]

    #test separators between pairs: space, comma, both or a mix
    pairs = unpack_feeds_str("binance oc ADA/USDT BTC/USDT")[2]
    assert pairs == ["ADA/USDT", "BTC/USDT"]
    
    pairs = unpack_feeds_str("binance oc ADA/USDT,BTC/USDT")[2]
    assert pairs == ["ADA/USDT", "BTC/USDT"]
    
    pairs = unpack_feeds_str("binance oc ADA/USDT, BTC/USDT")[2]
    assert pairs == ["ADA/USDT", "BTC/USDT"]
    
    pairs = unpack_feeds_str("binance oc ADA/USDT BTC/USDT,ETH/USDC, DOT/DAI")[2]
    assert pairs == ["ADA/USDT", "BTC/USDT", "ETH/USDC", "DOT/DAI"]

