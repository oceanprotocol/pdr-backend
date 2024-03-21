from typing import Dict, List, Union
from enforce_typing import enforce_types
from pdr_backend.cli.arg_feeds import ArgFeeds


@enforce_types
class PredictFeedMixin:
    FEEDS_KEY = "feeds"

    def __init__(self, d: dict):
        self.d = d

    def parse_feed_obj(self, feed_obj: Union[str, list]) -> ArgFeeds:
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

        parsed_objs = []
        for feed in feed_obj:
            # Convert each feed_obj string to ArgFeeds
            feed_obj = ArgFeeds.from_str(feed)
            parsed_objs.extend(feed_obj)
        return parsed_objs

    @property
    def feeds(self) -> List[Dict[str, ArgFeeds]]:
        feeds_list = []
        for feed in self.d.get(self.__class__.FEEDS_KEY, []):
            predict = feed.get("predict", "")
            train_on = feed.get("train_on", [])

            predict_feeds = self.parse_feed_obj(predict)
            train_on_feeds = self.parse_feed_obj(train_on)

            feeds_list.append({"predict": predict_feeds, "train_on": train_on_feeds})

        return feeds_list
