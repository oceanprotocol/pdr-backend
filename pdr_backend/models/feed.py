from typing import Any, Dict, List

from enforce_typing import enforce_types

from pdr_backend.util.strutil import StrMixin


class Feed(StrMixin):  # pylint: disable=too-many-instance-attributes
    @enforce_types
    def __init__(
        self,
        name: str,
        address: str,
        symbol: str,
        seconds_per_epoch: int,
        seconds_per_subscription: int,
        trueval_submit_timeout: int,
        owner: str,
        pair: str,
        timeframe: str,
        source: str,
    ):
        self.name = name
        self.address = address
        self.symbol = symbol
        self.seconds_per_epoch = seconds_per_epoch
        self.seconds_per_subscription = seconds_per_subscription
        self.trueval_submit_timeout = trueval_submit_timeout
        self.owner = owner
        self.pair = pair
        self.timeframe = timeframe
        self.source = source

    @property
    def base(self):
        return self._splitpair()[0]

    @property
    def quote(self):
        return self._splitpair()[1]

    @enforce_types
    def _splitpair(self) -> List[str]:
        pair = self.pair.replace("/", "-")
        return pair.split("-")

    @enforce_types
    def shortstr(self) -> str:
        return (
            f"[Feed {self.address[:7]} {self.pair}" f"|{self.source}|{self.timeframe}]"
        )

    @enforce_types
    def __str__(self) -> str:
        return self.shortstr()


@enforce_types
def dictToFeed(feed_dict: Dict[str, Any]):
    """
    @description
      Convert a feed_dict into Feed format

    @arguments
      feed_dict -- dict with values for "name", "address", etc

    @return
      feed -- Feed
    """
    d = feed_dict
    feed = Feed(
        name=d["name"],
        address=d["address"],
        symbol=d["symbol"],
        seconds_per_epoch=int(d["seconds_per_epoch"]),
        seconds_per_subscription=int(d["seconds_per_subscription"]),
        trueval_submit_timeout=int(d["trueval_submit_timeout"]),
        owner=d["owner"],
        pair=d["pair"],
        timeframe=d["timeframe"],
        source=d["source"],
    )
    return feed
