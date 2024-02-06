import json
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from unittest.mock import Mock

import addresses
from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.contract.slot import Slot
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.subgraph.subgraph_feed_contracts import query_feed_contracts
from pdr_backend.subgraph.subgraph_pending_slots import get_pending_slots
from pdr_backend.util.contract import _condition_sapphire_keys, get_contract_filename
from pdr_backend.util.strutil import StrMixin
from pdr_backend.util.web3_config import Web3Config


# pylint: disable=too-many-public-methods
class Web3PP(StrMixin):
    __STR_OBJDIR__ = ["network", "d"]

    @enforce_types
    def __init__(self, d: dict, network: str):
        if network not in d:
            raise ValueError(f"network '{network}' not found in dict")

        self.network = network  # e.g. "sapphire-testnet", "sapphire-mainnet"
        self.d = d  # yaml_dict["web3_pp"]

        self._web3_config: Optional[Web3Config] = None

    # --------------------------------
    # JIT cached properties - only do the work if requested
    #   (and therefore don't complain if missing envvar)

    @property
    def web3_config(self) -> Web3Config:
        if self._web3_config is None:
            rpc_url = self.rpc_url
            private_key = os.getenv("PRIVATE_KEY")
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
    def query_feed_contracts(self) -> Dict[str, SubgraphFeed]:
        """
        @description
          Gets all feeds, only filtered by self.owner_addrs

        @return
          feeds -- dict of [feed_addr] : SubgraphFeed
        """
        feeds = query_feed_contracts(
            subgraph_url=self.subgraph_url,
            owners_string=self.owner_addrs,
        )
        # postconditions
        for feed in feeds.values():
            assert isinstance(feed, SubgraphFeed)
        return feeds

    @enforce_types
    def get_contracts(self, feed_addrs: List[str]) -> Dict[str, Any]:
        """
        @description
          Get contracts for specified feeds

        @arguments
          feed_addrs -- which feeds we want

        @return
          contracts -- dict of [feed_addr] : PredictoorContract
        """
        # pylint: disable=import-outside-toplevel
        from pdr_backend.contract.predictoor_contract import PredictoorContract

        contracts = {}
        for addr in feed_addrs:
            contracts[addr] = PredictoorContract(self, addr)
        return contracts

    @enforce_types
    def get_pending_slots(
        self,
        timestamp: int,
        allowed_feeds: Optional[ArgFeeds] = None,
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
            allowed_feeds=allowed_feeds,
        )

    @enforce_types
    def tx_call_params(self, gas=None) -> dict:
        call_params = {
            "from": self.web3_config.owner,
            "gasPrice": self.tx_gas_price(),
        }
        if gas is not None:
            call_params["gas"] = gas
        return call_params

    @enforce_types
    def tx_gas_price(self) -> int:
        """Return gas price for use in call_params of transaction calls."""
        network = self.network
        if network in ["sapphire-testnet", "sapphire-mainnet"]:
            return self.web3_config.w3.eth.gas_price
            # return 100000000000
        if network in ["development", "barge-predictoor-bot", "barge-pytest"]:
            return 0
        raise ValueError(f"Unknown network {network}")

    @enforce_types
    def get_address(self, contract_name: str) -> str:
        network = self.get_addresses()
        if not network:
            raise ValueError(f'Cannot find network "{self.network}" in addresses.json')

        address = network.get(contract_name)
        if not address:
            error = (
                f'Cannot find contract "{contract_name}" in address.json '
                f'for network "{self.network}"'
            )
            raise ValueError(error)

        return address

    @enforce_types
    def get_addresses(self) -> Union[dict, None]:
        """
        Returns addresses in web3_pp.address_file, in web3_pp.network
        """
        address_file = self.address_file

        path = None
        if address_file:
            address_file = os.path.expanduser(address_file)
            path = Path(address_file)
        else:
            path = Path(str(os.path.dirname(addresses.__file__)) + "/address.json")

        if not path.exists():
            raise TypeError(f"Cannot find address.json file at {path}")

        with open(path) as f:
            d = json.load(f)

        d = _condition_sapphire_keys(d)

        if "barge" in self.network:  # eg "barge-pytest"
            return d["development"]

        if self.network in d:  # eg "development", "oasis_sapphire"
            return d[self.network]

        return None

    @property
    def OCEAN_address(self) -> str:
        return self.get_address("Ocean")

    @property
    def OCEAN_Token(self) -> Token:
        return Token(self, self.OCEAN_address)

    @property
    def NativeToken(self) -> NativeToken:
        return NativeToken(self)

    def get_token_balance(self, address):
        return self.web3_config.w3.eth.get_balance(address)

    def get_contract_abi(self, contract_name: str):
        """
        Returns the ABI for the specified contract
        """
        path = get_contract_filename(contract_name, self.address_file)

        if not path.exists():
            raise TypeError("Contract name does not exist in artifacts.")

        with open(path) as f:
            data = json.load(f)
            return data["abi"]


# =========================================================================
# utilities for testing


@enforce_types
def mock_web3_pp(network: str) -> Web3PP:
    D1 = {
        "address_file": "address.json 1",
        "rpc_url": "http://example.com/rpc",
        "subgraph_url": "http://example.com/subgraph",
        "owner_addrs": "0xOwner1",
    }
    D = {
        network: D1,
    }
    return Web3PP(D, network)


@enforce_types
def inplace_mock_feedgetters(web3_pp, feed: SubgraphFeed):
    # pylint: disable=import-outside-toplevel
    from pdr_backend.contract.predictoor_contract import mock_predictoor_contract

    inplace_mock_query_feed_contracts(web3_pp, feed)

    c = mock_predictoor_contract(feed.address)
    inplace_mock_get_contracts(web3_pp, feed, c)


@enforce_types
def inplace_mock_query_feed_contracts(web3_pp: Web3PP, feed: SubgraphFeed):
    web3_pp.query_feed_contracts = Mock()
    web3_pp.query_feed_contracts.return_value = {feed.address: feed}


@enforce_types
def inplace_mock_get_contracts(
    web3_pp: Web3PP, feed: SubgraphFeed, predictoor_contract
):
    # pylint: disable=import-outside-toplevel
    from pdr_backend.contract.predictoor_contract import PredictoorContract

    assert isinstance(predictoor_contract, PredictoorContract)
    web3_pp.get_contracts = Mock()
    web3_pp.get_contracts.return_value = {feed.address: predictoor_contract}


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
        self,
        predicted_value: bool,
        stake_amt: float,
        prediction_ts: int,
        wait_for_receipt: bool = True,
    ):  # pylint: disable=unused-argument
        assert stake_amt <= 3
        if prediction_ts in self._prediction_slots:
            print(f"      (Replace prev pred at time slot {prediction_ts})")
        self._prediction_slots.append(prediction_ts)


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
        "pdr_backend.contract.predictoor_contract.PredictoorContract",
        mock_contract_func,
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
