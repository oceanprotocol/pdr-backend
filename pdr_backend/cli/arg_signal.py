from typing import List, Set, Union

from enforce_typing import enforce_types

from pdr_backend.util.constants import CHAR_TO_SIGNAL


class ArgSignal:
    @enforce_types
    def __init__(self, signal_str: str):
        """
        @arguments
          signal_str -- e.g. "close"
        """
        if signal_str not in CHAR_TO_SIGNAL.values():
            raise ValueError(signal_str)

        self.signal_str = signal_str

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self.signal_str

    @staticmethod
    def from_char(char: str) -> "ArgSignal":
        """eg given "o", return "open" """
        if char not in CHAR_TO_SIGNAL:
            raise ValueError()

        return ArgSignal(CHAR_TO_SIGNAL[char])

    def to_char(self) -> str:
        inv_map = {v: k for k, v in CHAR_TO_SIGNAL.items()}
        return inv_map[self.signal_str]


class ArgSignals(List[ArgSignal]):
    @enforce_types
    def __init__(self, signals: List[Union[str, ArgSignal]]):
        """
        @arguments
          signals -- e.g. ["open", "high"]
        """
        if not signals:
            raise ValueError(signals)

        super().__init__([ArgSignal(signal_str) for signal_str in signals])

    @staticmethod
    def from_str(signals_str: str) -> "ArgSignals":
        signal_str_list = [CHAR_TO_SIGNAL[c] for c in signals_str]
        return ArgSignals(signal_str_list)

    @property
    def signal_strs(self) -> Set[str]:
        return set(str(signal) for signal in self)

    @enforce_types
    def contains(self, signal: Union[str, ArgSignal]) -> bool:
        return ArgSignal(signal) in self

    # old signals_to_chars
    def to_chars(self) -> str:
        """
        Example: Given {"high", "close", "open"}
        Return "ohc"
        """
        chars = ""
        signal_strs = [str(signal) for signal in self]

        for cand_signal in CHAR_TO_SIGNAL.values():
            if cand_signal in signal_strs:
                c = ArgSignal(cand_signal).to_char()
                chars += c

        return chars


# ==========================================================================
# verify..() functions


@enforce_types
def verify_signalchar_str(signalchar_str: str, graceful: bool = False):
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
            if graceful:
                return False

            raise ValueError(signalchar_str)
        c_seen.add(c)

    return True
