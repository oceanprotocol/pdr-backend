#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List, Dict

from enforce_typing import enforce_types
from typeguard import check_type

from pdr_backend.cli.arg_feed import ArgFeed
from pdr_backend.cli.arg_feeds import ArgFeeds


class PredictTrainFeedset:
    """
    Easy manipulation of a single set of (predict feed / train_on feeds).

    To be precise, it has:
    - 1 feed to predict
    - >=1 feeds as inputs to the model
    """

    @enforce_types
    def __init__(
        self, predict: ArgFeed, train_on: ArgFeeds, ta_features: List[str] = None
    ):
        self.predict: ArgFeed = predict
        self.train_on: ArgFeeds = train_on
        self.ta_features: List[str] = ta_features if ta_features else []

    @enforce_types
    def __str__(self) -> str:
        return str(self.to_dict())

    @enforce_types
    def __eq__(self, other):
        return (
            self.predict == other.predict
            and self.train_on == other.train_on
            and self.ta_features == other.ta_features
        )

    @enforce_types
    def to_dict(self) -> Dict[str, str]:
        return {
            "predict": str(self.predict),
            "train_on": str(self.train_on),
            "ta_features": str(self.ta_features),
        }

    @classmethod
    def from_dict(cls, feedset_dict: dict) -> "PredictTrainFeedset":
        """
        @arguments
          feedset_dict -- has the following format:
            {"predict":predict_feed_str (1 feed),
             "train_on":train_on_feeds_str (>=1 feeds),
             "ta_features":list of extra features}
            Note just ONE predict feed is allowed, not >=1.

          Here are three examples. from_dict() gives the same output for each.
          1. { "predict" : "binance BTC/USDT o 1h",
               "train_on" : "binance BTC/USDT ETH/USDT o 1h"}
          2. { "predict" : "binance BTC/USDT o 1h",
                "train_on" : "binance BTC/USDT o 1h, binance ETH/USDT o 1h"}
          3. { "predict" : "binance BTC/USDT o 1h",
               "train_on" : ["binance BTC/USDT o 1h", "binance ETH/USDT o 1h"],
               "ta_features": ["rsi", "macd"]}
        """
        predict = ArgFeed.from_str(feedset_dict["predict"])
        train_on = ArgFeeds.from_strs(_as_list(feedset_dict.get("train_on")))
        ta_features = feedset_dict.get("ta_features", [])
        check_type(ta_features, List[str])
        return cls(predict, train_on, ta_features)

    @property
    def timeframe_ms(self) -> int:
        """Returns timeframe, in ms"""
        return self.predict.timeframe.ms if self.predict.timeframe else 0


@enforce_types
def _as_list(str_or_list) -> List[str]:
    """Given a str or a list of str, always returns as a list"""
    if isinstance(str_or_list, str):
        return [str_or_list]
    check_type(str_or_list, List[str])  # raises TypeCheckError if wrong type
    return str_or_list
