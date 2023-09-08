from os import getenv

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig


@enforce_types
class TraderConfig(BaseConfig):
    def __init__(self):
        super().__init__()

        self.trader_min_buffer = int(getenv("TRADER_MIN_BUFFER", "60"))
        self.max_tries = 10
