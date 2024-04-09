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


@enforce_types
class PredictFeed:
    def __init__(self, predict: ArgFeed, train_on: ArgFeeds):
        self.predict: ArgFeed = predict
        self.train_on: ArgFeeds = train_on

    @classmethod
    def from_feed_objs(cls, predict: ArgFeed, train_on: Union[str, list]):
        parsed_train_on: ArgFeeds = parse_feed_obj(train_on)
        return cls(predict, parsed_train_on)

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
    def predict_quote_str(self) -> Optional[str]:
        return ArgPair(self.predict.pair).quote_str

    @property
    def predict_base_str(self) -> Optional[str]:
        return ArgPair(self.predict.pair).base_str

    @property
    def predict_pair_str(self) -> Optional[str]:
        return ArgPair(self.predict.pair).pair_str


@enforce_types
class PredictFeeds(List[PredictFeed]):
    def __init__(self, feeds: List[PredictFeed]):
        super().__init__(feeds)

    @classmethod
    def from_array(cls, feeds: List[dict]):
        fin = []
        for pairs in feeds:
            predict = pairs.get("predict")
            train_on = pairs.get("train_on")
            if train_on is None:
                raise ValueError(f"train_on must be provided, got {pairs}")
            if predict is None:
                raise ValueError(f"predict must be provided, got {pairs}")
            predict = parse_feed_obj(predict)
            for p in predict:
                fin.append(PredictFeed.from_feed_objs(p, train_on))
        return cls(fin)

    @property
    def feeds_str(self) -> List[str]:
        set_pairs = []
        for feed in self:
            for pairs in [feed.train_on]:
                for pair in pairs:
                    if str(pair) not in set_pairs:
                        set_pairs.append(str(pair))
            if str(feed.predict) not in set_pairs:
                set_pairs.append(str(feed.predict))
        return set_pairs

    @property
    def feeds(self) -> List[ArgFeed]:
        set_pairs = []
        for feed in self:
            for pairs in [feed.train_on]:
                for pair in pairs:
                    if pair not in set_pairs:
                        set_pairs.append(pair)
            if feed.predict not in set_pairs:
                set_pairs.append(feed.predict)
        return set_pairs

    @property
    def min_epoch_seconds(self) -> int:
        epoch = 1e9
        for feed in self:
            assert feed.predict.timeframe is not None, f"Feed: {feed} is is missing timeframe"
            epoch = min(epoch, feed.predict.timeframe.s)
        return int(epoch)

    def to_list(self) -> List[dict]:
        return [feed.to_dict() for feed in self]
