import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_pair import (
    ArgPair,
    ArgPairs,
    _unpack_pairs_str,
    _verify_base_str,
    _verify_quote_str,
)


@enforce_types
def test_arg_pair_main():
    # basic tests
    p1 = ArgPair("BTC/USDT")
    p2 = ArgPair(base_str="BTC", quote_str="USDT")
    assert p1.pair_str == p2.pair_str == "BTC/USDT"
    assert p1.base_str == p2.base_str == "BTC"
    assert p1.quote_str == p2.quote_str == "USDT"

    # test __eq__
    assert p1 == p2
    assert p1 == "BTC/USDT"

    assert p1 != ArgPair("ETH/USDT")
    assert p1 != "ETH/USDT"
    assert p1 != 3

    # test __str__
    assert str(p1) == "BTC/USDT"
    assert str(p2) == "BTC/USDT"


@enforce_types
def test_unpack_pair_str():
    assert ArgPair("BTC/USDT").base_str == "BTC"
    assert ArgPair("BTC/USDT").quote_str == "USDT"
    assert ArgPair("BTC-USDT").base_str == "BTC"
    assert ArgPair("BTC-USDT").quote_str == "USDT"


@enforce_types
def test_unpack_pairs_str():
    with pytest.raises(ValueError):
        _unpack_pairs_str("")

    assert ArgPairs.from_str("ADA-USDT BTC/USDT") == ["ADA/USDT", "BTC/USDT"]
    assert ArgPairs.from_str("ADA/USDT,BTC/USDT") == ["ADA/USDT", "BTC/USDT"]
    assert ArgPairs.from_str("ADA/USDT, BTC/USDT") == ["ADA/USDT", "BTC/USDT"]
    assert ArgPairs.from_str("ADA/USDT BTC/USDT,ETH-USDC, DOT/DAI") == [
        "ADA/USDT",
        "BTC/USDT",
        "ETH/USDC",
        "DOT/DAI",
    ]


@enforce_types
def test_pack_pair_str_list():
    assert str(ArgPairs(["ADA/USDT"])) == "ADA/USDT"
    assert str(ArgPairs(["ADA-USDT"])) == "ADA/USDT"
    assert str(ArgPairs(["ADA/USDT", "BTC/USDT"])) == "ADA/USDT,BTC/USDT"
    assert str(ArgPairs(["ADA/USDT", "BTC-USDT"])) == "ADA/USDT,BTC/USDT"
    assert str(ArgPairs(["ADA-USDT", "BTC-USDT"])) == "ADA/USDT,BTC/USDT"

    with pytest.raises(TypeError):
        ArgPairs("")

    with pytest.raises(ValueError):
        ArgPairs([])

    with pytest.raises(TypeError):
        ArgPairs(None)

    with pytest.raises(ValueError):
        ArgPairs(["adfs"])

    with pytest.raises(ValueError):
        ArgPairs(["ADA-USDT fgds"])

    pair_from_base_and_quote = ArgPair(base_str="BTC", quote_str="USDT")
    assert str(ArgPair(pair_from_base_and_quote)) == "BTC/USDT"


@enforce_types
def test_verify_pairs_str__and__verify_pair_str():
    # ok for verify_pairs_str, ok for verify_pair_str
    # (well-formed 1 pair)
    strs = [
        "BTC/USDT",
        "BTC-USDT",
        "ETH/USDT",
        "BTC/RAI",
        "BTC/DAI",
        " BTC/USDT",
        "BTC/USDT ",
        "  BTC/USDT   ",
    ]

    for pair_str in strs:
        ArgPair(pair_str)

    for pair_str in strs:
        ArgPairs([pair_str])

    # not ok for verify_pair_str, ok for verify_pairs_str
    # (well-formed >1 signal or >1 pair)
    strs = [
        "ADA/USDT BTC/USDT",
        "ADA/USDT,BTC/USDT",
        "ADA/USDT, BTC/USDT",
        "ADA/USDT ,BTC/USDT",
        "ADA/USDT , BTC/USDT",
        "ADA/USDT  ,  BTC/USDT",
        "    ADA/USDT  ,  BTC/USDT   ",
        "ADA/USDT, BTC/USDT ETH-USDC , DOT/DAI",
    ]
    for pairs_str in strs:
        ArgPairs.from_str(pairs_str)
    for pair_str in strs:
        with pytest.raises(ValueError):
            ArgPair(pair_str)

    # not ok for verify_pair_str, not ok for verify_pairs_str
    # (poorly formed)
    strs = [
        "",
        "  ",
        ",",
        "x",
        "/",
        "  x  ",
        "  ,  ",
        "  /  ",
        "BTC/",
        "BTC /",
        "BTC / ",
        "/USDT",
        "/ USDT",
        " / USDT",
        "BTC-",
        "-USDT",
        "BTC/ USDT",
        "BTC /USDT",
        "BTC / USDT",
        "BTC/XYZ",
        "BTC//USDT",
        "BTC--USDT",
        "BTC-/USDT",
        "BTC/-USDT",
        "BTC/USDT/",
        "BTC/USDT-",
        "BTC/USDT/USDT",
        "BTC/USDT-USDT",
        "ADA/USDT & BTC/USDT",
        "ADA/USDT x BTC/USDT",
        "ADA/USDT : BTC/USDT",
        "ADA/USDT BTC/USDT XYZ",
        "ADA/USDT XYZ BTC/USDT",
        "ADA/USDT BTC/ BTC/USDT",
        "ADA/USDT - BTC/USDT",
        "ADA/USDT / BTC/USDT",
    ]

    for pairs_str in strs:
        with pytest.raises(ValueError):
            ArgPairs.from_str(pairs_str)
        with pytest.raises(ValueError):
            ArgPair(pairs_str)


@enforce_types
def test_base_str():
    # ok
    strs = [
        "ETH",
        "  ETH",
        "ETH",
        "  ETH  ",
        "BTC",
        "ADA",
        "OCEAN",
    ]
    for base_str in strs:
        _verify_base_str(base_str)

    # not ok
    strs = [
        "",
        "  ",
        ",",
        "Eth",
        "eth",
        "ETH:",
        "ETH/",
        "ET:H",
        "ET/H",
        "ET&H",
    ]
    for base_str in strs:
        with pytest.raises(ValueError):
            _verify_base_str(base_str)


@enforce_types
def test_quote_str():
    # ok
    strs = [
        "USDT",
        "  USDT",
        "USDT",
        "  USDT  ",
        "USDC",
        "RAI",
        "DAI",
    ]
    for quote_str in strs:
        _verify_quote_str(quote_str)

    # not ok
    strs = [
        "",
        "  ",
        ",",
        "Usdt",
        "usdt",
        "USDT:",
        "USDT/",
        "US:DT",
        "US/DT",
        "US&DT",
    ]
    for quote_str in strs:
        with pytest.raises(ValueError):
            _verify_quote_str(quote_str)
