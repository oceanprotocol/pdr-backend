from typing import List, Optional, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.arg_pair import ArgPair


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


class PredictTrainFeedset:
    """
    Easy manipulation of a single set of (predict feed / train_on feeds).

    To be precise, it has:
    - 1 feed to predict
    - >=1 feeds as inputs to the model
    """

    @enforce_types
    def __init__(self, predict_feed: ArgFeed, train_feeds: ArgFeeds):
        self.predict: ArgFeed = predict_feed
        self.train_on: ArgFeeds = train_feeds

    @classmethod
    def from_feed_objs(
        cls,
        predict_feed: ArgFeed,
        unparsed_train_feeds: Union[str, list],
    ):
        train_feeds: ArgFeeds = parse_feed_obj(unparsed_train_feeds)
        return cls(predict_feed, train_feeds)

    @enforce_types
    def to_dict(self):
        return {"predict": self.predict, "train_on": self.train_on}

    @classmethod
    def from_dict(cls, d):
        return cls(d["predict"], d["train_on"])

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.predict.timeframe.ms if self.predict.timeframe else 0

    @property
    def predict_pair_str(self) -> Optional[str]:
        pair: ArgPair = self.predict.pair
        return pair.pair_str
