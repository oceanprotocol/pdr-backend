from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.models.feed import dictToFeed, Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot
from pdr_backend.util.env import getenv_or_exit, parse_filters
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.subgraph import get_pending_slots, query_feed_contracts
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class BaseConfig(StrMixin):
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.rpc_url: str = getenv_or_exit("RPC_URL")  # type: ignore
        self.subgraph_url: str = getenv_or_exit("SUBGRAPH_URL")  # type: ignore
        self.private_key: str = getenv_or_exit("PRIVATE_KEY")  # type: ignore

        (f0, f1, f2, f3) = parse_filters()
        self.pair_filters: [List[str]] = f0
        self.timeframe_filter: [List[str]] = f1
        self.source_filter: [List[str]] = f2
        self.owner_addresses: [List[str]] = f3

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

    def get_feeds(self) -> Dict[str, Feed]:
        """Return dict of [feed_addr] : {"name":.., "pair":.., ..}"""
        feed_dicts = query_feed_contracts(
            self.subgraph_url,
            ",".join(self.pair_filters),
            ",".join(self.timeframe_filter),
            ",".join(self.source_filter),
            ",".join(self.owner_addresses),
        )
        feeds = {addr: dictToFeed(feed_dict) for addr, feed_dict in feed_dicts.items()}
        return feeds

    def get_contracts(self, feed_addrs: List[str]) -> Dict[str, PredictoorContract]:
        """Return dict of [feed_addr] : PredictoorContract}"""
        contracts = {}
        for addr in feed_addrs:
            contracts[addr] = PredictoorContract(self.web3_config, addr)
        return contracts
