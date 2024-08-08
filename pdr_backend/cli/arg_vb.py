from typing import List, Union

from enforce_typing import enforce_types

class ArgVB:
    @enforce_types
    def __init__(self, vb_str: str):
        """
        @arguments
          vb_str -- e.g. "2100"
        """
        vb_float_ok(vb_str)

        self.vb_str = vb_str

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
          Parses a comma-separated string of volume_thresholds, e.g. "105.3,200"
        """
        if not isinstance(volume_thresholds_str, str):
            raise TypeError("volume_thresholds_str must be a string")

        return ArgVBs(volume_thresholds_str.split(","))

    def __str__(self):
        if not self:
            return ""

        return ",".join([str(vb) for vb in self])


@enforce_types
def vb_float_ok(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False