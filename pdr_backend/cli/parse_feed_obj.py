from typing import List, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


@enforce_types
def parse_feed_obj(feed_obj: Union[str, list]) -> ArgFeeds:
    # If feed_obj is a string, convert to list
    if isinstance(feed_obj, str):
        # If comma separated string, split
        # If not comma separated, convert to list
        if "," in feed_obj:
            feed_obj = feed_obj.split(",")
        else:
            feed_obj = [feed_obj]

    if not isinstance(feed_obj, list):
        raise ValueError(f"feed_obj must be a list, got {feed_obj}")

    parsed_objs: ArgFeeds = ArgFeeds([])
    for feed in feed_obj:
        # Convert each feed_obj string to ArgFeeds
        arg_feeds: List[ArgFeed] = ArgFeeds.from_str(str(feed))
        parsed_objs.extend(arg_feeds)
    return parsed_objs
