from os import getenv
from typing import Dict, List, Optional

from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.types import BlockData

from pdr_backend.models.feed import dictToFeed, Feed
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot
from pdr_backend.util.env import getenv_or_exit, parse_filters
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.subgraph import get_pending_slots, query_feed_contracts
from pdr_backend.util.web3_config import Web3Config


class Web3PP(StrMixin):
    __STR_OBJDIR__ = ["network", "d"]

    @enforce_types
    def __init__(self, network: str, d: dict):
        if network not in d:
            raise ValueError(f"network '{network}' not found in dict")

        self.network = network  # e.g. "sapphire-testnet", "sapphire-mainnet"
        self.d = d  # yaml_dict["data_pp"]

        self._web3_config = None

    # --------------------------------
    # JIT cached properties - only do the work if requested
    #   (and therefore don't complain if missing envvar)

    @property
    def web3_config(self) -> Web3Config:
        if self._web3_config is None:
            rpc_url = self.rpc_url
            private_key = getenv("PRIVATE_KEY")
            self._web3_config = Web3Config(rpc_url, private_key)
        return self._web3_config

    # --------------------------------
    # yaml properties
    @property
    def dn(self) -> str:  # "d at network". Compact on purpose.
        return self.d[self.network]

    @property
    def address_file(self) -> str:
        return self.dn["address_file"]

    @property
    def rpc_url(self) -> str:
        return self.dn["rpc_url"]

    @property
    def subgraph_url(self) -> str:
        return self.dn["subgraph_url"]

    @property
    def stake_token(self) -> str:
        return self.dn["stake_token"]

    @property
    def owner_addrs(self) -> str:
        return self.dn["owner_addrs"]

    # --------------------------------
    # setters (add as needed)
    @enforce_types
    def set_web3_config(self, web3_config):
        self._web3_config = web3_config

    # --------------------------------
    # derived properties
    @property
    def private_key(self) -> Optional[str]:
        return self.web3_config.private_key

    @property
    def account(self) -> Optional[LocalAccount]:
        return self.web3_config.account

    @property
    def w3(self) -> Optional[Web3]:
        return self.web3_config.w3

    @property
    def get_block(self, *args, **kwargs) -> BlockData:
        return self.web3_config.get_block(*args, **kwargs)

    # --------------------------------
    # onchain feed data
    @enforce_types
    def get_contracts(self, feed_addrs: List[str]) -> Dict[str, PredictoorContract]:
        """
        @description
          Get contracts for specified feeds

        @arguments
          feed_addrs -- which feeds we want

        @return
          contract -- dict of [feed_addr] : PredictoorContract
        """
        contracts = {}
        for addr in feed_addrs:
            contracts[addr] = PredictoorContract(self.web3_config, addr)
        return contracts

    @enforce_types
    def get_feeds(
        self,
        pair_filters: Optional[List[str]] = None,
        timeframe_filters: Optional[List[str]] = None,
        source_filters: Optional[List[str]] = None,
    ) -> Dict[str, Feed]:
        """
        @description
          Query chain to get Feeds

        @arguments
          pair_filters -- filter to these pairs. eg ["BTC/USDT", "ETH/USDT"]
          timeframe_filters -- filter to just these timeframes. eg ["5m", "1h"]
          source_filters -- filter to just these exchanges. eg ["binance"]

        @return
          feeds -- dict of [feed_addr] : Feed
        """
        feed_dicts = query_feed_contracts(
            self.subgraph_url,
            pair_filters,
            timeframe_filters,
            source_filters,
            [self.owner_addrs],
        )
        feeds = {addr: dictToFeed(feed_dict) for addr, feed_dict in feed_dicts.items()}
        return feeds

    @enforce_types
    def get_pending_slots(
        self,
        timestamp: int,
        pair_filters: Optional[List[str]] = None,
        timeframe_filter: Optional[List[str]] = None,
        source_filter: Optional[List[str]] = None,
    ) -> List[Slot]:
        """
        @description
          Query chain to get Slots that have status "Pending".

        @return
          pending_slots -- List[Slot]
        """
        return get_pending_slots(
            self.subgraph_url,
            timestamp,
            self.owner_addrs,
            pair_filters,
            timeframe_filter,
            source_filter,
        )
