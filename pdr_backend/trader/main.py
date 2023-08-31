from os import getenv
import time
from typing import Dict, List
from enforce_typing import enforce_types

from pdr_backend.models.predictoor_contract import PredictoorContract
from pdr_backend.trader.trade import trade
from pdr_backend.util.env import getenv_or_exit
from pdr_backend.util.subgraph import query_predictContracts
from pdr_backend.util.web3_config import Web3Config


class TraderConfig:
    def __init__(self):
        self.rpc_url: str = getenv_or_exit("RPC_URL")
        self.subgraph_url: str = getenv_or_exit("SUBGRAPH_URL")
        self.private_key: str = getenv_or_exit("PRIVATE_KEY")

        self.pair_filters: str = getenv("PAIR_FILTER")
        self.timeframe_filter: str = getenv("TIMEFRAME_FILTER")
        self.source_filter: str = getenv("SOURCE_FILTER")
        self.owner_addresses: str = getenv("OWNER_ADDRS")

        self.s_until_epochs_end = int(getenv("SECONDS_TILL_EPOCH_END", "60"))

        self.web3_config: Web3Config = Web3Config(
            self.rpc_url, self.private_key
        )

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
            contracts[address] = PredictoorContract(self.web3_config, address)

        return contracts


class Trader:
    def __init__(self):
        self.config = TraderConfig()
        self.feeds = self.config.get_feeds()  # [addr] : feed
        self._addrs = list(self.feeds.keys())
        self.contracts = self.config.get_contracts(self._addrs)  # [addr] : contract

        self.prev_block_time: int = 0
        self.prev_block_number: int = 0
        self.prev_submitted_epochs = {addr: 0 for addr in self._addrs}

    def run(self):
        print("Starting main loop...")
        while True:
            self.take_step()

    def take_step(self):
        w3 = self.config.web3_config.w3

        # at new block number yet?
        block_number = w3.eth.block_number
        if block_number <= self.prev_block_number:
            time.sleep(1)
            return
        self.prev_block_number = block_number

        # is new block ready yet?
        block = w3.eth.get_block(block_number, full_transactions=False)
        if not block:
            return
        self.prev_block_time = block["timestamp"]
        print(f"Got new block, with number {block_number} ")

        # do work at new block
        for addr in self._addrs:
            self._process_block_at_feed(addr, block["timestamp"])

    def _process_block_at_feed(self, addr: str, timestamp: str):
        # base data
        feed = self.feeds[addr]
        predictoor_contract = self.contracts[addr]
        epoch = predictoor_contract.get_current_epoch()
        s_per_epoch = predictoor_contract.get_secondsPerEpoch()
        s_remaining_in_epoch = epoch * s_per_epoch + s_per_epoch - timestamp

        # print status
        print(
            f"{feed['name']} at address {addr}"
            f" is at epoch {epoch}"
            f". s_per_epoch: {s_per_epoch}, "
            f"s_remaining_in_epoch: {s_remaining_in_epoch}"
        )

        if epoch > self.prev_submitted_epochs[addr] > 0:
            prediction = predictoor_contract.get_agg_predval(
                epoch * s_per_epoch
            )
            print(f"Got {prediction}.")
            if prediction is not None:
                trade(feed, prediction)


@enforce_types
def main():
    trader = Trader()
    trader.run()


if __name__ == "__main__":
    main()
