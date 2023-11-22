from enforce_typing import enforce_types
from pdr_backend.util.strutil import StrMixin


class TruevalSS(StrMixin):
    __STR_OBJDIR__ = ["d"]
    
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["trueval_ss"]

    # --------------------------------
    # yaml properties
    @property
    def sleep_time(self) -> int:
        """# seconds to wait between batches"""
        return self.d["sleep_time"]

    @property
    def batch_size(self) -> int:
        """# slots to process in a batch"""
        return self.d["batch_size"]
