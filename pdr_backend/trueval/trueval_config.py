from os import getenv
from typing import Optional, List

from enforce_typing import enforce_types
from pdr_backend.models.slot import Slot

from pdr_backend.util.env import getenv_or_exit, parse_filters
from pdr_backend.util.subgraph import get_pending_slots
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class TruevalConfig:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.rpc_url: str = getenv_or_exit("RPC_URL")  # type: ignore
        self.subgraph_url: str = getenv_or_exit("SUBGRAPH_URL")  # type: ignore
        self.private_key: str = getenv_or_exit("PRIVATE_KEY")  # type: ignore

        filters = parse_filters()
        self.pair_filters: Optional[List[str]] = filters[0]  # type: ignore
        self.timeframe_filter: Optional[List[str]] = filters[1]  # type: ignore
        self.source_filter: Optional[List[str]] = filters[2]  # type: ignore

        owner_addresses_var = filters[3]
        if owner_addresses_var is None:
            raise Exception("Owner addresses are required.")
        self.owner_addresses: List[str] = owner_addresses_var  # type: ignore

        self.web3_config = Web3Config(self.rpc_url, self.private_key)

        self.sleep_time = int(getenv("SLEEP_TIME", "30"))
        self.batch_size = int(getenv("BATCH_SIZE", "30"))

    def get_pending_slots(self, timestamp: int) -> List[Slot]:
        return get_pending_slots(
            self.subgraph_url,
            timestamp,
            self.owner_addresses,
            self.pair_filters,
            self.timeframe_filter,
            self.source_filter,
        )
