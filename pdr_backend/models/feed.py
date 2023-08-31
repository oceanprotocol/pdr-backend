from typing import Any, Dict

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
    def quote(self):
        return self.pair.split("-")[1]

    @property
    def base(self):
        return self.pair.split("-")[0]

    def shortstr(self) -> str:
        return \
            f"[Feed {self.address[:7]} / {self.pair}" \
            f" / {self.source} / {self.timeframe}]"

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
        seconds_per_epoch=d["seconds_per_epoch"],
        seconds_per_subscription=d["seconds_per_subscription"],
        trueval_submit_timeout=d["trueval_submit_timeout"],
        owner=d["owner"],
        pair=d["pair"],
        timeframe=d["timeframe"],
        source=d["source"],
    )
    return feed
