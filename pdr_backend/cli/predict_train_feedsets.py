from typing import List

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.parse_feed_obj import parse_feed_obj
from pdr_backend.cli.predict_train_feedset import PredictTrainFeedset


class PredictTrainFeedsets(List[PredictTrainFeedset]):
    """
    Easy manipulation of all (predict/train_on) PredictTrainFeedset objects.
    Includes a way to parse from the raw yaml inputs.
    """

    @enforce_types
    def __init__(self, feedsets: List[PredictTrainFeedset]):
        super().__init__(feedsets)

    @enforce_types
    def __str__(self) -> str:
        strs = [str(feedset) for feedset in self]
        return "[" + ", ".join(strs) + "]"

    @classmethod
    @enforce_types
    def from_list_of_dict(cls, feedset_list: List[dict]) -> "PredictTrainFeedsets":
        """
        @arguments
          feedset_list -- list of feedset_dict,
            where feedset_dict has the following format:
            {"predict":predict_feeds_str,
             "train_on":train_on_feeds_str}
            Note that >=1 predict feeds are allowed for a given feedset_dict.

          Example feedset_list = [
            {
                "predict": "binance BTC/USDT c 5m, kraken BTC/USDT c 5m",
                "train_on": [
                    "binance BTC/USDT ETH/USDT DOT/USDT c 5m",
                    "kraken BTC/USDT c 5m",
                ],
            },
            {
                "predict": "binance ETH/USDT ADA/USDT c 5m",
                "train_on": "binance BTC/USDT DOT/USDT c 5m, kraken BTC/USDT c 5m",
            },
        """
        final_list = []
        for feedset_dict in feedset_list:
            if not ("predict" in feedset_dict and "train_on" in feedset_dict):
                raise ValueError(feedset_dict)

            predict_feeds: ArgFeeds = parse_feed_obj(feedset_dict["predict"])
            for predict in predict_feeds:
                train_on = parse_feed_obj(feedset_dict["train_on"])
                feedset = PredictTrainFeedset(predict, train_on)
                final_list.append(feedset)

        return cls(final_list)

    @enforce_types
    def to_list_of_dict(self) -> List[dict]:
        """Like from_list_of_dict(), but in reverse"""
        return [feedset.to_dict() for feedset in self]

    @property
    def feed_strs(self) -> List[str]:
        """
        Return eg ['binance BTC/USDT DOT/USDT c 5m','kraken BTC/USDT c 5m']
        """
        return [str(feed) for feed in self.feeds]

    @property
    def feeds(self) -> List[ArgFeed]:
        feed_list = []
        for feedset in self:
            for train_feeds in [feedset.train_on]:
                for train_feed in train_feeds:
                    if train_feed not in feed_list:
                        feed_list.append(train_feed)

            predict_feed = feedset.predict
            if predict_feed not in feed_list:
                feed_list.append(predict_feed)

        return feed_list

    @property
    def min_epoch_seconds(self) -> int:
        epoch = 1e9
        for feedset in self:
            predict_feed = feedset.predict
            assert predict_feed.timeframe is not None, predict_feed

            epoch = min(epoch, predict_feed.timeframe.s)
        return int(epoch)

    @enforce_types
    def get_feedset(
        self,
        exchange_str: str,
        pair_str: str,
        timeframe_str: str,
    ):
        """
        @description
          Return a feedset if the input (exchange, pair, timeframe)
          is found in one of the predict feeds

         Example input: "binance", "BTC/USDT", "5m"
        """
        for feedset in self:
            predict_feed: ArgFeed = feedset.predict
            if (
                str(predict_feed.exchange) == exchange_str
                and str(predict_feed.pair) == pair_str
                and str(predict_feed.timeframe) == timeframe_str
            ):
                return feedset

        return None
