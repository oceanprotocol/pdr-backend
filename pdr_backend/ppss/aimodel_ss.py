import copy
from typing import List, Set, Tuple

import numpy as np
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feed import ArgFeeds
from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.util.strutil import StrMixin

APPROACHES = ["LIN", "GPR", "SVR", "NuSVR", "LinearSVR"]


@enforce_types
class AimodelSS(StrMixin):
    __STR_OBJDIR__ = ["d"]

    def __init__(self, d: dict):
        self.d = d  # yaml_dict["aimodel_ss"]

        # save self.exchs_dict
        self.exchs_dict: dict = {}  # e.g. {"binance" : ccxt.binance()}
        feeds = ArgFeeds.from_strs(self.input_feeds_strs)
        for feed in feeds:
            exchange_class = feed.exchange.exchange_class
            self.exchs_dict[str(feed.exchange)] = exchange_class()

        # test inputs
        if self.approach not in APPROACHES:
            raise ValueError(self.approach)

        assert 0 < self.max_n_train
        assert 0 < self.autoregressive_n < np.inf

    # --------------------------------
    # yaml properties
    @property
    def approach(self) -> str:
        return self.d["approach"]  # eg "LIN"

    @property
    def input_feeds_strs(self) -> List[str]:
        return self.d["input_feeds"]  # eg ["binance BTC/USDT ohlcv",..]

    @property
    def n_exchs(self) -> int:
        return len(self.exchs_dict)

    @property
    def exchange_strs(self) -> List[str]:
        return sorted(self.exchs_dict.keys())

    @property
    def n_input_feeds(self) -> int:
        return len(self.input_feeds)

    @property
    def input_feeds(self) -> ArgFeeds:
        """Return list of ArgFeed(exchange_str, signal_str, pair_str)"""
        return ArgFeeds.from_strs(self.input_feeds_strs)

    @property
    def max_n_train(self) -> int:
        return self.d["max_n_train"]  # eg 50000. S.t. what data is available

    @property
    def autoregressive_n(self) -> int:
        return self.d[
            "autoregressive_n"
        ]  # eg 10. model inputs ar_n past pts z[t-1], .., z[t-ar_n]

    @property
    def exchange_pair_tups(self) -> Set[Tuple[str, str]]:
        """Return set of unique (exchange_str, pair_str) tuples"""
        return set((feed.exchange, str(feed.pair)) for feed in self.input_feeds)

    @property
    def n(self) -> int:
        """Number of input dimensions == # columns in X"""
        return self.n_input_feeds * self.autoregressive_n

    @enforce_types
    def copy_with_yval(self, data_pp: DataPP):
        """Copy self, add data_pp's feeds to new data_ss' inputs as needed"""
        d2 = copy.deepcopy(self.d)

        for predict_feed in data_pp.predict_feeds:
            if predict_feed in self.input_feeds:
                continue
            d2["input_feeds"].append(str(predict_feed))

        return AimodelSS(d2)
