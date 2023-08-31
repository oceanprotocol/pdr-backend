from typing import Dict, List, Optional

from enforce_typing import enforce_types

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot
from pdr_backend.util.env import getenv_or_exit, parse_filters
from pdr_backend.util.subgraph import get_pending_slots, query_feed_contracts
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class BaseConfig:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.rpc_url: str = getenv_or_exit("RPC_URL")  # type: ignore
        self.subgraph_url: str = getenv_or_exit("SUBGRAPH_URL")  # type: ignore
        self.private_key: str = getenv_or_exit("PRIVATE_KEY")  # type: ignore

        (
            pair_filter,
            timeframe_filter,
            source_filter,
            owner_addresses,
        ) = parse_filters()
        self.pair_filters: Optional[List[str]] = pair_filter  # type: ignore
        self.timeframe_filter: Optional[List[str]] = timeframe_filter  # type: ignore
        self.source_filter: Optional[List[str]] = source_filter  # type: ignore
        self.owner_addresses: Optional[List[str]] = owner_addresses  # type: ignore

        self.web3_config = Web3Config(self.rpc_url, self.private_key)

    def get_pending_slots(self, timestamp: int) -> List[Slot]:
        return get_pending_slots(
            self.subgraph_url,
            timestamp,
            self.owner_addresses,
            self.pair_filters,
            self.timeframe_filter,
            self.source_filter,
        )

    def get_feeds(self) -> Dict[str, dict]:
        """Return dict of [feed_addr] : {"name":.., "pair":.., ..}"""
        feeds_dict = query_feed_contracts(
            self.subgraph_url,
            self.pair_filters,
            self.timeframe_filter,
            self.source_filter,
            self.owner_addresses,
        )
        return feeds_dict

    def get_contracts(self, feed_addrs: List[str]) -> Dict[str, PredictoorContract]:
        """Return dict of [feed_addr] : PredictoorContract}"""
        contracts = {}
        for addr in feed_addrs:
            contracts[addr] = PredictoorContract(self.web3_config, addr)
        return contracts
