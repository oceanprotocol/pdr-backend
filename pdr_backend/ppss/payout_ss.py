from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class PayoutSS(StrMixin):
    @enforce_types
    def __init__(self, d: dict):
        self.d = d  # yaml_dict["trueval_ss"]

    # --------------------------------
    # yaml properties
    @property
    def batch_size(self) -> int:
        return self.d["batch_size"]
