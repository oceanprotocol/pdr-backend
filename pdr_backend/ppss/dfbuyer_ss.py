from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.util.strutil import StrMixin


class DFBuyerSS(MultiFeedMixin, StrMixin):
    __STR_OBJDIR__ = ["d"]
    FEEDS_KEY = "feeds"

    @enforce_types
    def __init__(self, d: dict):
        # yaml_dict["dfbuyer_ss"]
        super().__init__(d, assert_feed_attributes=["timeframe"])

    # --------------------------------
    # yaml properties
    @property
    def weekly_spending_limit(self) -> int:
        """
        Target consume amount in OCEAN per week
        """
        return self.d["weekly_spending_limit"]

    @property
    def batch_size(self) -> int:
        """
        Number of pairs to consume in a batch
        """
        return self.d["batch_size"]

    @property
    def consume_interval_seconds(self) -> int:
        """
        Frequency of consume in seconds
        """
        return self.d["consume_interval_seconds"]

    @property
    def max_request_tries(self) -> int:
        """
        Number of times to retry the request, hardcoded to 5
        """
        return 5

    # feeds defined in base

    # --------------------------------
    # derived values
    @property
    def amount_per_interval(self):
        return float(
            self.weekly_spending_limit / (7 * 24 * 3600) * self.consume_interval_seconds
        )
