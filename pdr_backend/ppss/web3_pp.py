from os import getenv
import random
from typing import Dict, List, Optional
from unittest.mock import Mock

from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3

from pdr_backend.models.feed import Feed
from pdr_backend.models.predictoor_contract import (
    mock_predictoor_contract,
    PredictoorContract,
)
from pdr_backend.models.slot import Slot
from pdr_backend.util.strutil import StrMixin
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
    def query_feed_contracts(self) -> Dict[str, Feed]:
        """
        @description
          Gets all feeds, only filtered by self.owner_addrs

        @return
          feeds -- dict of [feed_addr] : Feed
        """
        feeds = query_feed_contracts(
            subgraph_url=self.subgraph_url,
            owners_string=self.owner_addrs,
        )
        # postconditions
        for feed in feeds.values():
            assert isinstance(feed, Feed)
        return feeds

    @enforce_types
    def get_contracts(self, feed_addrs: List[str]) -> Dict[str, PredictoorContract]:
        """
        @description
          Get contracts for specified feeds

        @arguments
          feed_addrs -- which feeds we want

        @return
          contracts -- dict of [feed_addr] : PredictoorContract
        """
        contracts = {}
        for addr in feed_addrs:
            contracts[addr] = PredictoorContract(self, addr)
        return contracts

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


# =========================================================================
# utilities for testing


@enforce_types
def del_network_override(monkeypatch):
    if getenv("NETWORK_OVERRIDE"):
        monkeypatch.delenv("NETWORK_OVERRIDE")


@enforce_types
def mock_web3_pp(network: str) -> Web3PP:
    D1 = {
        "address_file": "address.json 1",
        "rpc_url": "http://example.com/rpc",
        "subgraph_url": "http://example.com/subgraph",
        "stake_token": "0xStake1",
        "owner_addrs": "0xOwner1",
    }
    D = {
        network: D1,
    }
    return Web3PP(D, network)


@enforce_types
def inplace_mock_feedgetters(web3_pp, feed: Feed):
    inplace_mock_query_feed_contracts(web3_pp, feed)

    c = mock_predictoor_contract(feed.address)
    inplace_mock_get_contracts(web3_pp, feed, c)


@enforce_types
def inplace_mock_query_feed_contracts(web3_pp: Web3PP, feed: Feed):
    web3_pp.query_feed_contracts = Mock()
    web3_pp.query_feed_contracts.return_value = {feed.address: feed}


@enforce_types
def inplace_mock_get_contracts(web3_pp: Web3PP, feed: Feed, c: PredictoorContract):
    web3_pp.get_contracts = Mock()
    web3_pp.get_contracts.return_value = {feed.address: c}


@enforce_types
class _MockEthWithTracking:
    def __init__(self, init_timestamp: int, init_block_number: int):
        self.timestamp: int = init_timestamp
        self.block_number: int = init_block_number
        self._timestamps_seen: List[int] = [init_timestamp]

    def get_block(
        self, block_number: int, full_transactions: bool = False
    ):  # pylint: disable=unused-argument
        mock_block = {"timestamp": self.timestamp}
        return mock_block


@enforce_types
class _MockPredictoorContractWithTracking:
    def __init__(self, w3, s_per_epoch: int, contract_address: str):
        self._w3 = w3
        self.s_per_epoch = s_per_epoch
        self.contract_address: str = contract_address
        self._prediction_slots: List[int] = []

    def get_current_epoch(self) -> int:
        """Returns an epoch number"""
        return self.get_current_epoch_ts() // self.s_per_epoch

    def get_current_epoch_ts(self) -> int:
        """Returns a timestamp"""
        return self._w3.eth.timestamp // self.s_per_epoch * self.s_per_epoch

    def get_secondsPerEpoch(self) -> int:
        return self.s_per_epoch

    def submit_prediction(
        self, predval: bool, stake: float, timestamp: int, wait: bool = True
    ):  # pylint: disable=unused-argument
        assert stake <= 3
        if timestamp in self._prediction_slots:
            print(f"      (Replace prev pred at time slot {timestamp})")
        self._prediction_slots.append(timestamp)


@enforce_types
def inplace_mock_w3_and_contract_with_tracking(
    web3_pp: Web3PP,
    init_timestamp: int,
    init_block_number: int,
    timeframe_s: int,
    feed_address: str,
    monkeypatch,
):
    """
    Updates web3_pp.web3_config.w3 with a mock.
    Includes a mock of time.sleep(), which advances the (mock) blockchain
    Includes a mock of web3_pp.PredictoorContract(); returns it for convenience
    """
    mock_w3 = Mock()  # pylint: disable=not-callable
    mock_w3.eth = _MockEthWithTracking(init_timestamp, init_block_number)
    _mock_pdr_contract = _MockPredictoorContractWithTracking(
        mock_w3,
        timeframe_s,
        feed_address,
    )

    mock_contract_func = Mock()
    mock_contract_func.return_value = _mock_pdr_contract
    monkeypatch.setattr(
        "pdr_backend.ppss.web3_pp.PredictoorContract", mock_contract_func
    )

    def advance_func(*args, **kwargs):  # pylint: disable=unused-argument
        do_advance_block = random.random() < 0.40
        if do_advance_block:
            mock_w3.eth.timestamp += random.randint(3, 12)
            mock_w3.eth.block_number += 1
            mock_w3.eth._timestamps_seen.append(mock_w3.eth.timestamp)

    monkeypatch.setattr("time.sleep", advance_func)

    assert hasattr(web3_pp.web3_config, "w3")
    web3_pp.web3_config.w3 = mock_w3

    return _mock_pdr_contract
