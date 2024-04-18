from typing import List, Optional, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.arg_pair import ArgPair


@enforce_types
def parse_feed_obj(feed_obj: Union[str, list]) -> ArgFeeds:
    # Create feed_list from feed_obj
    if isinstance(feed_obj, list):
        feed_list = feed_obj
    else:
        assert isinstance(feed_obj, str)
        # If comma separated string, split
        # If not comma separated, convert to list
        if "," in feed_obj:
            feed_list = feed_obj.split(",")
        else:
            feed_list = [feed_obj]

    if not isinstance(feed_list, list):
        raise ValueError(f"feed_list must be a list, got {feed_list}")

    parsed_arg_feeds: ArgFeeds = ArgFeeds([])
    for feed in feed_list:
        # Convert each feed string to ArgFeeds
        arg_feeds: List[ArgFeed] = ArgFeeds.from_str(str(feed))
        parsed_arg_feeds.extend(arg_feeds)

    return parsed_arg_feeds


class PredictTrainFeedset:
    """
    Easy manipulation of a single set of (predict feed / train_on feeds).

    To be precise, it has:
    - 1 feed to predict
    - >=1 feeds as inputs to the model
    """

    @enforce_types
    def __init__(self, predict: ArgFeed, train_on: ArgFeeds):
        self.predict: ArgFeed = predict
        self.train_on: ArgFeeds = train_on

    @classmethod
    def from_feed_objs(
        cls,
        predict: ArgFeed,
        unparsed_train_on: Union[str, list],
    ):
        train_on: ArgFeeds = parse_feed_obj(unparsed_train_on)
        return cls(predict, train_on)

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
