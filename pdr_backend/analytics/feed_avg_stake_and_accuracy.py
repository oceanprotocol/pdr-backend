from typing import Optional

import requests

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.util.currency_types import Eth


@enforce_types
def get_avg_stake_and_accuracy_for_feed(feed: ArgFeed) -> Optional[tuple]:
    feed_name = feed.pair.pair_str
    feed_name = feed_name.upper()
    feed_timeframe = feed.timeframe

    req = requests.get("https://websocket.predictoor.ai/statistics")

    data = req.json()

    for feed in data:
        if feed['alias'] == feed_timeframe:
            for _, value in feed['statistics'].items():
                if value['token_name'] == feed_name:
                    return value['average_accuracy'], Eth(value['total_staked_today'])

    return None

