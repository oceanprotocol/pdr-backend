import os
from os import getenv
import time

from enforce_typing import enforce_types

from pdr_backend.util.env import getenv_or_exit


@enforce_types
class PredictoorConfig:
    def __init__(self):
        self.rpc_url: str = getenv_or_exit("RPC_URL")
        self.subgraph_url: str = getenv_or_exit("SUBGRAPH_URL")
        self.private_key: str = getenv_or_exit("PRIVATE_KEY")
        
        self.pair_filters: str = getenv("PAIR_FILTER")
        self.timeframe_filter: str = getenv("TIMEFRAME_FILTER")
        self.source_filter: str = getenv("SOURCE_FILTER")
        self.owner_addresses: str = getenv("OWNER_ADDRS")
        
        self.s_until_epochs_end = int(os.getenv("SECONDS_TILL_EPOCH_END", "60"))
        self.stake_amount = int(os.getenv("STAKE_AMOUNT", "1"))

        self.web3_config: Web3Config = Web3Config(self.rpc_url, self.private_key)
        self.get_prediction = None # child needs to set this prediction function

    def get_feeds(self) -> Dict[str, dict]:
        """Return dict of [feed_addr] : {"name":.., "pair":.., ..}"""
        feeds_dict = query_predictContracts(
            self.subgraph_url,
            self.pair_filters,
            self.timeframe_filter,
            self.source_filter,
            self.owner_addresses,
        )
        return feeds_dict

    def get_contracts(self, feed_addrs: List[str]) \
            -> Dict[str, PredictoorContract]:
        """Return dict of [feed_addr] : PredictoorContract}"""
        contracts = {}
        for address in feed_addrs:
            contracts[address] = PredictoorContract(
                self.web3_config, address)
