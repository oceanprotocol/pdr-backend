from typing import List, Union

from enforce_typing import enforce_types


class ArgThreshold:
    def __init__(self, threshold_str: str):
        """
        @arguments
          threshold_str -- e.g. "vb_2100" "db_2090.5" "tb_208"
        """
        prefix, value_str = _unpack_threshold_str(threshold_str)

        if prefix not in ["vb", "db", "tb"]:
            raise ValueError("threshold should start with vb, db or tb")

        self.prefix = prefix  # 'db', 'vb', 'tb'
        self.value_str = value_str
        self.value = float(self.value_str)

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return self.prefix + "_" + self.value_str

    def threshold(self) -> float:
        return self.value


class ArgThresholds(List[ArgThreshold]):
    def __init__(self, thresholds: Union[List[str], List[ArgThreshold]]):
        if not isinstance(thresholds, list):
            raise TypeError("hresholds must be a list")

        thres = []
        for thre in thresholds:
            thre = ArgThreshold(thre) if isinstance(thre, str) else thre
            thres.append(thre)

        super().__init__(thres)

    @staticmethod
    def from_str(thresholds_str: str):
        """
        @description
          Parses a comma-separated string of thresholds, e.g. "vb-105.3,vb-200"
        """
        if not isinstance(thresholds_str, str):
            raise TypeError("thresholds_str must be a string")

        return ArgThresholds(thresholds_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(th) for th in self])


@enforce_types
def threshold_str_ok(s: str) -> bool:
    try:
        ArgThresholds.from_str(s)
        return True
    except ValueError:
        return False


@enforce_types
def verify_threshold_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgThreshold(s)


@enforce_types
def verify_thresholds_str(s: str):
    """Raise an error if input string is invalid."""
    _ = ArgThresholds.from_str(s)


def _unpack_threshold_str(th_str: str) -> tuple:
    """
    Unpacks the vb_str into prefix and value_str.

    Example: Given 'vb_2100.5'
    Return ('vb', '2100.5')
    """
    res = th_str.split("_")
    if len(res) != 2:
        raise ValueError("wrong format for threshold")
    prefix, value_str = res
    return (prefix, value_str)
