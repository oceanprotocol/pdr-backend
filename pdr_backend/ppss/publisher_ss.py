from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.ppss.base_ss import MultiFeedMixin
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed
from pdr_backend.util.strutil import StrMixin


class PublisherSS(MultiFeedMixin, StrMixin):
    @enforce_types
    def __init__(self, network: str, d: dict):
        self.network = network  # e.g. "sapphire-testnet", "sapphire-mainnet"
        self.__class__.FEEDS_KEY = network + ".feeds"
        super().__init__(
            d, assert_feed_attributes=["signal", "timeframe"]
        )  # yaml_dict["publisher_ss"]

    # --------------------------------
    # yaml properties
    @property
    def fee_collector_address(self) -> str:
        """
        Returns the address of FeeCollector of the current network
        """
        return self.d[self.network]["fee_collector_address"]


    @enforce_types
    def filter_feeds_from_candidates(
        self, cand_feeds: Dict[str, SubgraphFeed]
    ) -> Dict[str, SubgraphFeed]:
        raise NotImplementedError("PublisherSS should not filter subgraph feeds.")


@enforce_types
def mock_publisher_ss(network) -> PublisherSS:
    if network in ["development", "barge-pytest", "barge-predictoor-bot"]:
        feeds = ["binance BTC/USDT ETH/USDT XRP/USDT c 5m"]
    else:
        # sapphire-testnet, sapphire-mainnet
        feeds = [
            "binance BTC/USDT ETH/USDT BNB/USDT XRP/USDT"
            " ADA/USDT DOGE/USDT SOL/USDT LTC/USDT TRX/USDT DOT/USDT"
            " c 5m,1h"
        ]

    d = {
        network: {
            "fee_collector_address": "0x1",
            "feeds": feeds,
        }
    }
    return PublisherSS(network, d)
