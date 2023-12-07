from os import getenv
from typing import Dict, List, Optional

from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3

from pdr_backend.models.feed import dictToFeed, Feed, feed_dict_ok
from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.models.slot import Slot
from pdr_backend.util.exchangestr import pack_exchange_str_list
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.pairstr import pack_pair_str_list
from pdr_backend.util.timeframestr import pack_timeframe_str_list
from pdr_backend.util.subgraph import get_pending_slots, query_feed_contracts
from pdr_backend.util.web3_config import Web3Config


class Web3PP(StrMixin):
    __STR_OBJDIR__ = ["network", "d"]

    @enforce_types
    def __init__(self, d: dict, network: str):
        network = getenv("NETWORK_OVERRIDE") or network  # allow envvar override
        if network not in d:
            raise ValueError(f"network '{network}' not found in dict")

        self.network = network  # e.g. "sapphire-testnet", "sapphire-mainnet"
        self.d = d  # yaml_dict["data_pp"]

        self._web3_config: Optional[Web3Config] = None

    # --------------------------------
    # JIT cached properties - only do the work if requested
    #   (and therefore don't complain if missing envvar)

    @property
    def web3_config(self) -> Web3Config:
        if self._web3_config is None:
            rpc_url = self.rpc_url
            private_key = getenv("PRIVATE_KEY")
            self._web3_config = Web3Config(rpc_url, private_key)
        return self._web3_config  # type: ignore[return-value]

    # --------------------------------
    # yaml properties
    @property
    def dn(self) -> str:  # "d at network". Compact on purpose.
        return self.d[self.network]

    @property
    def address_file(self) -> str:
        return self.dn["address_file"]  # type: ignore[index]

    @property
    def rpc_url(self) -> str:
        return self.dn["rpc_url"]  # type: ignore[index]

    @property
    def subgraph_url(self) -> str:
        return self.dn["subgraph_url"]  # type: ignore[index]

    @property
    def stake_token(self) -> str:
        return self.dn["stake_token"]  # type: ignore[index]

    @property
    def owner_addrs(self) -> str:
        return self.dn["owner_addrs"]  # type: ignore[index]

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

    # keep off. @enforce_types
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
            subgraph_url=self.subgraph_url,
            pairs_string=pack_pair_str_list(pair_filters),
            timeframes_string=pack_timeframe_str_list(timeframe_filters),
            sources_string=pack_exchange_str_list(source_filters),
            owners_string=self.owner_addrs,
        )
        feeds = {
            addr: dictToFeed(feed_dict)
            for addr, feed_dict in feed_dicts.items()
            if feed_dict_ok(feed_dict)
        }
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
            subgraph_url=self.subgraph_url,
            timestamp=timestamp,
            owner_addresses=[self.owner_addrs] if self.owner_addrs else None,
            pair_filter=pair_filters,
            timeframe_filter=timeframe_filter,
            source_filter=source_filter,
        )


@enforce_types
def mock_web3_pp(network: str) -> Web3PP:
    """For unit tests"""
    D1 = {
        "address_file": "address.json 1",
        "rpc_url": "rpc url 1",
        "subgraph_url": "subgraph url 1",
        "stake_token": "0xStake1",
        "owner_addrs": "0xOwner1",
    }
    D = {
        network: D1,
    }
    return Web3PP(D, network)
