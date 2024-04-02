from typing import Dict, List, Optional
from enforce_typing import enforce_types
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_feeds import PredictFeeds


@enforce_types
class PredictFeedMixin:
    FEEDS_KEY = "feeds"

    def __init__(self, d: dict, assert_feed_attributes: Optional[List] = None):
        assert self.__class__.FEEDS_KEY
        self.d = d
        self.feeds = PredictFeeds.from_array(self.d.get(self.__class__.FEEDS_KEY, []))
        if assert_feed_attributes:
            missing_attributes = []
            for attr in assert_feed_attributes:
                for feed in self.feeds.feeds:
                    if not getattr(feed, attr):
                        missing_attributes.append(attr)

            if missing_attributes:
                raise AssertionError(
                    f"Missing attributes {missing_attributes} for some feeds."
                )
