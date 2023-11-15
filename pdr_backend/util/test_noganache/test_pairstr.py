from enforce_typing import enforce_types
import pytest

from pdr_backend.util.pairstr import (
    unpack_pairs_str,
    unpack_pair_str,
    verify_pairs_str,
    verify_pair_str,
    verify_base_str,
    verify_quote_str,
)

# ==========================================================================
# unpack..() functions


@enforce_types
def test_unpack_pair_str():
    assert unpack_pair_str("BTC/USDT") == ("BTC", "USDT")
    assert unpack_pair_str("BTC-USDT") == ("BTC", "USDT")


@enforce_types
def test_unpack_pairs_str():
    assert unpack_pairs_str("ADA-USDT BTC/USDT") == ["ADA-USDT", "BTC-USDT"]
    assert unpack_pairs_str("ADA/USDT,BTC/USDT") == ["ADA-USDT", "BTC-USDT"]
    assert unpack_pairs_str("ADA/USDT, BTC/USDT") == ["ADA-USDT", "BTC-USDT"]
    assert unpack_pairs_str("ADA/USDT BTC/USDT,ETH-USDC, DOT/DAI") == [
        "ADA-USDT",
        "BTC-USDT",
        "ETH-USDC",
        "DOT-DAI",
    ]


# ==========================================================================
# verify..() functions


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
    for pairs_str in strs:
        verify_pairs_str(pairs_str)
    for pair_str in strs:
        verify_pair_str(pair_str)

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
        verify_pairs_str(pairs_str)
    for pair_str in strs:
        with pytest.raises(ValueError):
            verify_pair_str(pair_str)

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
            verify_pairs_str(pairs_str)

    for pair_str in strs:
        with pytest.raises(ValueError):
            verify_pair_str(pair_str)


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
        verify_base_str(base_str)

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
            verify_base_str(base_str)


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
        verify_quote_str(quote_str)

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
            verify_quote_str(quote_str)
