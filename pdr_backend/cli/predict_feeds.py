from typing import List, Union
from pdr_backend.cli.arg_feeds import ArgFeeds


class PredictFeed:
    def __init__(self, predict: ArgFeeds, train_on: ArgFeeds):
        self.predict: ArgFeeds = predict
        self.train_on: ArgFeeds = train_on

    @classmethod
    def from_feed_objs(cls, predict: Union[str, list], train_on: Union[str, list]):
        parsed_predict = cls.parse_feed_obj(predict)
        parsed_train_on = cls.parse_feed_obj(train_on)
        return cls(parsed_predict, parsed_train_on)

    @staticmethod
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

        parsed_objs = []
        for feed in feed_obj:
            # Convert each feed_obj string to ArgFeeds
            feed_obj = ArgFeeds.from_str(feed)
            parsed_objs.extend(feed_obj)
        return parsed_objs

    def to_dict(self):
        return {
            "predict": self.predict,
            "train_on": self.train_on
        }
    
    def from_dict(d):
        return PredictFeed(d["predict"], d["train_on"])
        

class PredictFeeds(List[PredictFeed]):
    def __init__(self, feeds: List[PredictFeed]):
        super().__init__(feeds)

    @classmethod
    def from_array(cls, feeds: List[dict]):
        return cls([PredictFeed.from_feed_objs(feeds["predict"], feeds["train_on"]) for feeds in feeds])

    @property
    def feeds(self) -> List[str]:
        set_pairs = []
        for feed in self:
            for pair in [feed.predict, feed.train_on]:
                if str(pair) not in set_pairs:
                    set_pairs.extend([str(i) for i in pair])
        return set_pairs

    def to_list(self) -> List[dict]:
        return [feed.to_dict() for feed in self]