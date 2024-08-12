import re
from typing import List, Union

from enforce_typing import enforce_types


class ArgVB:
    def __init__(self, vb_str: str):
        """
        @arguments
          vb_str -- e.g. "vb_2100"
        """
        if not re.match(r"vb_\d+(\.\d+)?$", vb_str):
            raise ValueError("volume threshold must start with 'vb_' + float")

        _, value_str = _unpack_vb_str(vb_str)
        try:
            float(value_str)
        except ValueError:
            raise ValueError(f"Invalid float value: '{value_str}'")

        self.vb_str = vb_str

    def __eq__(self, other):
        return self.vb_str == str(other)

    def __str__(self):
        return self.vb_str


class ArgVBs(List[ArgVB]):
    def __init__(self, volume_thresholds: Union[List[str], List[ArgVB]]):
        if not isinstance(volume_thresholds, list):
            raise TypeError("volume_thresholds must be a list")

        vbs = []
        for vb in volume_thresholds:
            vb = ArgVB(vb) if isinstance(vb, str) else vb
            vbs.append(vb)

        super().__init__(vbs)

    @staticmethod
    def from_str(volume_thresholds_str: str):
        """
        @description
          Parses a comma-separated string of volume_thresholds, e.g. "vb-105.3,vb-200"
        """
        if not isinstance(volume_thresholds_str, str):
            raise TypeError("volume_thresholds_str must be a string")

        return ArgVBs(volume_thresholds_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(vb) for vb in self])


@enforce_types
def vb_str_ok(s: str) -> bool:
    try:
        ArgVBs.from_str(s)
        return True
    except ValueError:
        return False


@enforce_types
def verify_vb_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgVB(s)


@enforce_types
def verify_vbs_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgVBs.from_str(s)


def _unpack_vb_str(vb_str: str) -> tuple:
    """
    Unpacks the vb_str into prefix and value_str.

    Example: Given 'vb_2100.5'
    Return ('vb', '2100.5')
    """
    prefix, value_str = vb_str.split("_", 1)
    return (prefix, value_str)
