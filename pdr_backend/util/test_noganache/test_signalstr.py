from enforce_typing import enforce_types
import pytest

from pdr_backend.util.signalstr import (
    unpack_signalchar_str,
    verify_signalchar_str,
    verify_signal_str,
)


# ==========================================================================
# unpack..() functions


@enforce_types
def test_unpack_signalchar_str():
    tups = [
        ("o", ["open"]),
        ("h", ["high"]),
        ("l", ["low"]),
        ("c", ["close"]),
        ("v", ["volume"]),
        ("oh", ["open", "high"]),
        ("cv", ["close", "volume"]),
        ("ohlcv", ["open", "high", "low", "close", "volume"]),
    ]
    for signalchar_str, target_signal_str_list in tups:
        assert unpack_signalchar_str(signalchar_str) == target_signal_str_list


# ==========================================================================
# verify..() functions


@enforce_types
def test_verify_signalchar_str():
    # ok
    strs = [
        "o",
        "h",
        "l",
        "c",
        "v",
        "oh",
        "cv",
        "ov",
        "ohlcv",
        "vo",  # any order is ok
        "vohlc",
    ]
    for signalchar_str in strs:
        verify_signalchar_str(signalchar_str)

    # not ok
    strs = [
        "",
        "  ",
        ",",
        "x",
        "  x  ",
        " oh",
        "oh ",
        " oh ",
        "O",
        "OH",
        "ohlcV",
        "ohLc",
        "ohohl",
        "oh l",
        "ohlcvx",
        "oh x",
        "o,h",
    ]
    for signalchar_str in strs:
        with pytest.raises(ValueError):
            verify_signalchar_str(signalchar_str)


@enforce_types
def test_verify_signal_str():
    # ok
    strs = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    for signal_str in strs:
        verify_signal_str(signal_str)

    # not ok
    strs = [
        "",
        "  ",
        "xyz",
        "Open",
        "OPEN",
        "  open  ",
        "opeN",
        "op en",
    ]
    for signal_str in strs:
        with pytest.raises(ValueError):
            verify_signal_str(signal_str)
