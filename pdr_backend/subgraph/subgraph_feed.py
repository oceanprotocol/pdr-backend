import logging
import random
from typing import Dict, Optional

import ccxt
from enforce_typing import enforce_types

from pdr_backend.cli.arg_pair import ArgPair
from pdr_backend.cli.timeframe import Timeframe
from pdr_backend.util.strutil import StrMixin


logger = logging.getLogger("subgraph_feed")


class SubgraphFeed(StrMixin):  # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        name: str,  # eg 'Feed: binance | BTC/USDT | 5m'
        address: str,  # eg '0x123'
        symbol: str,  # eg 'binance-BTC/USDT-5m'
        seconds_per_subscription: int,  # eg 60 * 60 * 24
        trueval_submit_timeout: int,  # eg 60
        owner: str,  # eg '0x456'
        pair: str,  # eg 'BTC/USDT'
        timeframe: str,  # eg '5m'
        source: str,  # eg 'binance'
    ):
        self.name: str = name
        self.address: str = address
        self.symbol: str = symbol
        self.seconds_per_subscription: int = seconds_per_subscription
        self.trueval_submit_timeout: int = trueval_submit_timeout
        self.owner: str = owner
        self.pair: str = pair.replace("-", "/")
        self.timeframe: str = timeframe
        self.source: str = source

    @property
    def seconds_per_epoch(self):
        return Timeframe(self.timeframe).s

    @property
    def base(self):
        return ArgPair(self.pair).base_str

    @property
    def quote(self):
        return ArgPair(self.pair).quote_str

    @enforce_types
    def shortstr(self) -> str:
        return f"Feed: {self.timeframe} {self.source} {self.pair} {self.address}"

    def ccxt_exchange(self, *args, **kwargs) -> ccxt.Exchange:
        exchange_class = getattr(ccxt, self.source)
        return exchange_class(*args, **kwargs)

    @enforce_types
    def __str__(self) -> str:
        return self.shortstr()


@enforce_types
def print_feeds(feeds: Dict[str, SubgraphFeed], label: Optional[str] = None):
    label = label or "feeds"
    logger.info("%s %s:", len(feeds), label)
    if not feeds:
        logger.warning("<no feeds>")
        return
    for feed in feeds.values():
        logger.info("%s", feed)


# =========================================================================
# utilities for testing


@enforce_types
def _rnd_eth_addr() -> str:
    """Generate a random address with Ethereum format."""
    addr = "0x" + "".join([str(random.randint(0, 9)) for i in range(40)])
    return addr


@enforce_types
def mock_feed(timeframe_str: str, exchange_str: str, pair_str: str) -> SubgraphFeed:
    addr = _rnd_eth_addr()
    name = f"Feed {addr} {pair_str}|{exchange_str}|{timeframe_str}"
    feed = SubgraphFeed(
        name=name,
        address=addr,
        symbol=f"SYM: {addr}",
        seconds_per_subscription=86400,
        trueval_submit_timeout=60,
        owner="0xowner",
        pair=pair_str,
        timeframe=timeframe_str,
        source=exchange_str,
    )
    return feed
