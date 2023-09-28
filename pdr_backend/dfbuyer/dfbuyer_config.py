from os import getenv

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig


@enforce_types
class DFBuyerConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.weekly_spending_limit = int(getenv("WEEKLY_SPENDING_LIMIT", "37000"))
        self.consume_interval_seconds = int(getenv("CONSUME_INTERVAL_SECONDS", "86400"))

        # number of consumes to execute in a single transaction
        self.batch_size = int(getenv("CONSUME_BATCH_SIZE", "20"))

        self.amount_per_interval = float(
            self.weekly_spending_limit / (7 * 24 * 3600) * self.consume_interval_seconds
        )

        self.max_request_tries = 5
