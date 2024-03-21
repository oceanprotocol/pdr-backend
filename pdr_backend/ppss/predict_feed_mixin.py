from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


class PredictFeedMixin:
    FEEDS_KEY = "feeds"

    def __init__(self, d: dict):
        self.d = d

    @property
    def feeds(self) -> ArgFeeds:
        """
        Overriding feeds to return ArgFeeds based on the custom 'predict' and 'train_on' structure.
        """
        feeds_list = []
        for feed in self.d.get(self.__class__.FEEDS_KEY, []):
            predict = feed.get("predict", "")
            train_on = feed.get("train_on", [])

            predict = ArgFeed.from_str(predict)

            # If train_on is a string, convert to list for uniform processing
            if isinstance(train_on, str):
                if "," in train_on:
                    train_on = train_on.split(",")
                else:
                    train_on = [train_on]

            if not isinstance(train_on, list):
                raise ValueError(f"train_on must be a list, got {train_on}")

            train_on_objs = []
            for feed in train_on:
                train_on_obj = ArgFeeds.from_str(feed)
                train_on_objs.extend(train_on_obj)

            feeds_list.append({"predict": predict, "train_on": train_on_objs})

        return feeds_list