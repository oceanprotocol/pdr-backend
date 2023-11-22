from enforce_typing import enforce_types
from pdr_backend.util.strutil import StrMixin


class TruevalSS(StrMixin):
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["trueval_ss"]

    # --------------------------------
    # yaml properties
    @property
    def sleep_time(self) -> int:
        return self.d["sleep_time"]  # number of seconds to wait between batches

    @property
    def batch_size(self) -> int:
        return self.d["batch_size"]  # how many slots to process in a batch
