from typing import List, Optional, Union

from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.arg_pair import ArgPair
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

    @classmethod
    def from_array(cls, feedset_list: List[dict]) -> "PredictTrainFeedsets":
        """
        @arguments
          feedset_list -- yaml-parsed list of dicts, where each entry has
            a "predict" and "train_on" item. Example below.

        @return
          PredictTrainFeedsets

        @notes

        Example 'feedset_list' = [
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
        return_list = []
        for feedset_dict in feedset_list:
            predict_dict = feedset_dict.get("predict")
            train_dict = feedset_dict.get("train_on")
            if train_dict is None:
                raise ValueError(f"train_on must be provided, got {feedset_dict}")
            if predict_dict is None:
                raise ValueError(f"predict must be provided, got {feedset_dict}")
            predict_feeds: ArgFeeds = parse_feed_obj(predict_dict)
            for predict_feed in predict_feeds:
                predict_train_feedset = PredictTrainFeedset.from_feed_objs(
                    predict_feed, train_dict
                )
                return_list.append(predict_train_feedset)
                
        return cls(return_list)

    @property
    def feeds_str(self) -> List[str]:
        str_list = []
        for predict_train_feedset in self:
            for train_feeds in [predict_train_feedset.train_on]:
                for train_feed in train_feeds:
                    if str(train_feed) not in str_list:
                        str_list.append(str(train_feed))

            predict_feed = predict_train_feedset.predict
            if str(predict_feed) not in str_list:
                str_list.append(str(predict_feed))
                
        return str_list

    @property
    def feeds(self) -> List[ArgFeed]:
        feed_list = []
        for predict_train_feedset in self:
            for train_feeds in [predict_train_feedset.train_on]:
                for train_feed in train_feeds:
                    if train_feed not in feed_list:
                        feed_list.append(train_feed)

            predict_feed = predict_train_feedset.predict
            if predict_feed not in feed_list:
                feed_list.append(predict_feed)
        return feed_list

    @property
    def min_epoch_seconds(self) -> int:
        epoch = 1e9
        for predict_train_feedset in self:
            predict_feed = predict_train_feedset.predict
            assert predict_feed.timeframe is not None, \
                f"Predict feed: {predict_feed} is missing timeframe"
            epoch = min(epoch, predict_feed.timeframe.s)
        return int(epoch)

    @enforce_types
    def to_list(self) -> List[dict]:
        return [predict_train_feedset.to_dict()
                for predict_train_feedset in self]
