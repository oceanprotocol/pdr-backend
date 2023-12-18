from enforce_typing import enforce_types
from web3 import Web3

from pdr_backend.subgraph.info725 import (
    key_to_key725,
    value_to_value725,
    value725_to_value,
    info_to_info725,
    info725_to_info,
)


@enforce_types
def test_key():
    key = "name"
    key725 = key_to_key725(key)
    assert key725 == Web3.keccak(key.encode("utf-8")).hex()


@enforce_types
def test_value():
    value = "ETH/USDT"
    value725 = value_to_value725(value)
    value_again = value725_to_value(value725)

    assert value == value_again
    assert value == Web3.to_text(hexstr=value725)


@enforce_types
def test_value_None():
    assert value_to_value725(None) is None
    assert value725_to_value(None) is None


@enforce_types
def test_info_to_info725_and_back():
    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": "binance"}
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": value_to_value725("binance")},
    ]
    assert info_to_info725(info) == info725
    assert info725_to_info(info725) == info


@enforce_types
def test_info_to_info725_and_back__some_None():
    info = {"pair": "BTC/USDT", "timeframe": "5m", "source": None}
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": None},
    ]
    assert info_to_info725(info) == info725
    assert info725_to_info(info725) == info


@enforce_types
def test_info_to_info725__extraval():
    info = {
        "pair": "BTC/USDT",
        "timeframe": "5m",
        "source": "binance",
        "extrakey": "extraval",
    }
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": value_to_value725("binance")},
        {"key": key_to_key725("extrakey"), "value": value_to_value725("extraval")},
    ]
    assert info_to_info725(info) == info725


@enforce_types
def test_info_to_info725__missingkey():
    info = {"pair": "BTC/USDT", "timeframe": "5m"}  # no "source"
    info725 = [
        {"key": key_to_key725("pair"), "value": value_to_value725("BTC/USDT")},
        {"key": key_to_key725("timeframe"), "value": value_to_value725("5m")},
        {"key": key_to_key725("source"), "value": None},
    ]
    assert info_to_info725(info) == info725
