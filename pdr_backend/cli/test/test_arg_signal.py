import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_signal import ArgSignal, ArgSignals, verify_signalchar_str

# ==========================================================================
# conversions


@enforce_types
def test_single_conversions():
    tups = [
        ("o", "open"),
        ("h", "high"),
        ("l", "low"),
        ("c", "close"),
        ("v", "volume"),
    ]
    for char, signal in tups:
        assert ArgSignal.from_char(char) == ArgSignal(signal)

    with pytest.raises(ValueError):
        ArgSignal("xyz")

    with pytest.raises(ValueError):
        ArgSignal.from_char("x")


@enforce_types
def test_multi_conversions():
    assert ArgSignals(["open"]).to_chars() == "o"
    assert ArgSignals(["close", "open"]).to_chars() == "oc"


# ==========================================================================
# unpack..() functions


@enforce_types
def test_fromstr():
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
        sig = ArgSignals.from_str(signalchar_str)
        assert sig == ArgSignals(target_signal_str_list)


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
        ArgSignal(signal_str)

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
            ArgSignal(signal_str)
