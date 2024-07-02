from typing import Optional

import requests

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.util.currency_types import Eth


@enforce_types
def get_avg_stake_and_accuracy_for_feed(feed: ArgFeed) -> Optional[tuple]:
    """
    Returns a tuple of:
        average accuracy (1 week average for 5m and 4 weeks for 1h feeds)
        total staked tokens in a day for the given feed.
    """
    feed_name = feed.pair.pair_str
    feed_name = feed_name.upper()
    feed_timeframe = feed.timeframe

    req = requests.get("https://websocket.predictoor.ai/statistics")

    data = req.json()

    for feed_data in data:
        if feed_data["alias"] == feed_timeframe:
            for _, value in feed_data["statistics"].items():
                if value["token_name"] == feed_name:
                    return float(value["average_accuracy"]) / 100, Eth(
                        value["total_staked_today"]
                    )

    return None
