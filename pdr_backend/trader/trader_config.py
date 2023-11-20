from os import getenv

from enforce_typing import enforce_types



@enforce_types
class TraderConfig(BaseConfig):
    def __init__(self):
        super().__init__()

        # Sets a threshold (in seconds) for trade decisions.
        # For example, if set to 180 and there's 179 seconds left, no trade. If 181, then trade.
        self.trader_min_buffer = int(getenv("TRADER_MIN_BUFFER", "60"))

        # Maximum attempts to process a feed
        self.max_tries = 10
