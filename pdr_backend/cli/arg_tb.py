import re
from typing import List, Union

from enforce_typing import enforce_types


# Tick Bar
class ArgTB:
    def __init__(self, tb_str: str):
        """
        @arguments
          tb_str -- e.g. "tb_2100"
        """
        if not re.match(r"tb_\d+(\.\d+)?$", tb_str):
            raise ValueError("ticks threshold must start with 'tb_' + int")

        _, value_str = _unpack_tb_str(tb_str)
        try:
            int(value_str)
        except ValueError:
            raise ValueError(f"Invalid int value: '{value_str}'")

        self.tb_str = tb_str

    def __eq__(self, other):
        return self.tb_str == str(other)

    def __str__(self):
        return self.tb_str

    def threshold(self) -> int:
        return int(self.tb_str.split("_")[1])


class ArgTBs(List[ArgTB]):
    def __init__(self, tick_thresholds: Union[List[str], List[ArgTB]]):
        if not isinstance(tick_thresholds, list):
            raise TypeError("tick_thresholds must be a list")

        tbs = []
        for tb in tick_thresholds:
            tb = ArgTB(tb) if isinstance(tb, str) else tb
            tbs.append(tb)

        super().__init__(tbs)

    @staticmethod
    def from_str(tick_thresholds_str: str):
        """
        @description
          Parses a comma-separated string of tick_thresholds, e.g. "tb-105,tb-200"
        """
        if not isinstance(tick_thresholds_str, str):
            raise TypeError("tick_thresholds_str must be a string")

        return ArgTBs(tick_thresholds_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(tb) for tb in self])


@enforce_types
def tb_str_ok(s: str) -> bool:
    try:
        ArgTBs.from_str(s)
        return True
    except ValueError:
        return False


@enforce_types
def verify_tb_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgTB(s)


@enforce_types
def verify_tbs_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgTBs.from_str(s)


def _unpack_tb_str(tb_str: str) -> tuple:
    """
    Unpacks the tb_str into prefix and value_str.

    Example: Given 'tb_2100'
    Return ('tb', '2100')
    """
    prefix, value_str = tb_str.split("_", 1)
    return (prefix, value_str)
