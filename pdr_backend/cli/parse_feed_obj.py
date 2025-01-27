from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


@enforce_types
def parse_feed_obj(feed_obj: Union[str, list]) -> ArgFeeds:
    # Create feed_list
    if isinstance(feed_obj, list):
        feed_list = feed_obj
    elif isinstance(feed_obj, str):
        if "," in feed_obj:
            feed_list = feed_obj.split(",")
        else:
            feed_list = [feed_obj]
    else:
        raise ValueError(feed_obj)

    # Parse feed_list
    parsed_arg_feeds: ArgFeeds = ArgFeeds([])
    for feed in feed_list:
        arg_feeds: List[ArgFeed] = ArgFeeds.from_str(str(feed))
        parsed_arg_feeds.extend(arg_feeds)

    return parsed_arg_feeds
