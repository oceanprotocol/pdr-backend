from typing import Dict, List, Optional, Union
from enforce_typing import enforce_types
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_feeds import PredictFeeds


@enforce_types
class PredictFeedMixin:
    FEEDS_KEY = "feeds"

    def __init__(self, d: dict, assert_feed_attributes: Optional[List] = None):
        self.d = d

        if assert_feed_attributes:
            pass  # TODO
            # missing_attributes = []
            # for attr in assert_feed_attributes:
            #     for feed in feeds:
            #         if not getattr(feed, attr):
            #             missing_attributes.append(attr)

            # if missing_attributes:
            #     raise AssertionError(
            #         f"Missing attributes {missing_attributes} for some feeds."
            #     )

    @property
    def feeds(self) -> List[Dict[str, ArgFeeds]]:
        feeds_list = PredictFeeds.from_array(self.d.get(self.__class__.FEEDS_KEY, []))
        return feeds_list.to_list()
