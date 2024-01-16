from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.strutil import StrMixin


@enforce_types
class TruevalSS(MultiFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEEDS_KEY = "feeds"

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

    # feeds defined in base
