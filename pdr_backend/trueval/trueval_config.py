from os import getenv

from enforce_typing import enforce_types

from pdr_backend.models.base_config import BaseConfig

@enforce_types
class TruevalConfig(BaseConfig):

    def __init__(self):
        super().__init__()
        
        if self.owner_addresses is None:
            raise Exception("Owner addresses are required.")
        
        self.sleep_time = int(getenv("SLEEP_TIME", "30"))
        self.batch_size = int(getenv("BATCH_SIZE", "30"))

