from typing import List

from enforce_typing import enforce_types

from pdr_backend.util.constants import CAND_SIGNALS, CHAR_TO_SIGNAL

# ==========================================================================
# conversions
@enforce_types
def char_to_signal(char: str) -> str:
    """eg given "o", return "open" """
    if char not in CHAR_TO_SIGNAL:
        raise ValueError()
    return CHAR_TO_SIGNAL[char]
    
@enforce_types
def signal_to_char(signal_str: str) -> str:
    """
    Example: Given "open"
    Return "o"
    """
    for c, s in CHAR_TO_SIGNAL.items():
        if s == signal_str:
            return c
    raise ValueError(signal_str)

# ==========================================================================
# unpack..() functions


@enforce_types
def unpack_signalchar_str(signalchar_str: str) -> List[str]:
    """
    @description
      Unpack a signalchar_str.

      Example: Given 'oh'
      Return ['open', 'high']

    @argument
      signalchar_str -- eg 'ohv'. A subset of 'ohlcv'

    @return
      signal_str_list -- List of signal_str
    """
    verify_signalchar_str(signalchar_str)
    signal_str_list = [CHAR_TO_SIGNAL[c] for c in signalchar_str]
    return signal_str_list


# ==========================================================================
# verify..() functions


@enforce_types
def verify_signalchar_str(signalchar_str: str):
    """
    @description
      Raise an error if signalchar_str is invalid

    @argument
      signalchar_str -- eg 'ohv'. A subset of 'ohlcv'
    """
    if len(signalchar_str) == 0:
        raise ValueError(signalchar_str)

    c_seen = set()
    for c in signalchar_str:
        if c not in "ohlcv" or c in c_seen:
            raise ValueError(signalchar_str)
        c_seen.add(c)


@enforce_types
def verify_signal_str(signal_str: str):
    """
    @description
      Raise an error if signal is invalid.

    @argument
      signal_str -- e.g. "close"
    """
    if signal_str not in CAND_SIGNALS:
        raise ValueError(signal_str)
