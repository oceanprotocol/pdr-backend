import re
from typing import List, Union

from enforce_typing import enforce_types


class ArgVB:
    def __init__(self, vb_str: str):
        """
        @arguments
          vb_str -- e.g. "vb-2100"
        """
        if not verify_vb_ok(vb_str):
            raise ValueError(vb_str)

        _, value_str = _unpack_vb_str(vb_str)

        self.vb_str = value_str

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self.vb_str


class ArgVBs(List[ArgVB]):
    @enforce_types
    def __init__(self, volume_thresholds: Union[List[str], List[ArgVB]]):
        if not isinstance(volume_thresholds, list):
            raise TypeError("volume_thresholds must be a list")

        volume_thresholds = []
        for vb in volume_thresholds:
            vb = ArgVB(vb) if isinstance(vb, str) else vb
            volume_thresholds.append(vb)

        super().__init__(volume_thresholds)

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
def verify_vb_ok(s: str, graceful: bool = False) -> bool:
    if not re.match(r"vb-\d+(\.\d+)?$", s):
        return False

    _, value_str = _unpack_vb_str(s)
    try:
        float(value_str)
        return True
    except ValueError:
        return False


def _unpack_vb_str(vb_str: str) -> tuple:
    """
    Unpacks the vb_str into prefix and value_str.

    Example: Given 'vb-2100.5'
    Return ('vb', '2100.5')
    """
    prefix, value_str = vb_str.split("-", 1)
    return (prefix, value_str)
