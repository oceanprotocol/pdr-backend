import os
import tempfile
from typing import List, Optional, Tuple

import yaml
from enforce_typing import enforce_types

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.cli.predict_feeds import PredictFeeds
from pdr_backend.ppss.dfbuyer_ss import DFBuyerSS
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.multisim_ss import MultisimSS
from pdr_backend.ppss.payout_ss import PayoutSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.publisher_ss import PublisherSS
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.ppss.topup_ss import TopupSS
from pdr_backend.ppss.trader_ss import TraderSS
from pdr_backend.ppss.trueval_ss import TruevalSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed, mock_feed
from pdr_backend.util.dictutil import recursive_update


@enforce_types
class PPSS:  # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        yaml_filename: Optional[str] = None,
        yaml_str: Optional[str] = None,
        network: Optional[str] = None,  # eg "development", "sapphire-testnet"
        nested_override_args: Optional[dict] = None,
        d: Optional[dict] = None,
    ):
        """
        @description
          Construct PPSS.

          The goal is to get a constructor dict 'd'; then fill the rest from d.

          Direct way:
          - pass in 'd'

          Or, indirect ways:
          - pass in 'yaml_filename' to load from a yaml file, or
          - pass in 'yaml_str' for contents like a yaml file
            (And optionally override some params with nested_override args)

          Whether direct or indirect, 'network' can be input (or default used).
        """
        # get constructor dict 'd'
        if d is None:
            d = self.constructor_dict(yaml_filename, yaml_str, nested_override_args)

        # fill from constructor dict 'd'
        self.lake_ss = LakeSS(d["lake_ss"])
        self.predictoor_ss = PredictoorSS(d["predictoor_ss"])
        self.trader_ss = TraderSS(d["trader_ss"])
        self.sim_ss = SimSS(d["sim_ss"])  # type: ignore
        self.multisim_ss = MultisimSS(d["multisim_ss"])
        self.publisher_ss = PublisherSS(d["publisher_ss"], network)
        self.trueval_ss = TruevalSS(d["trueval_ss"])
        self.dfbuyer_ss = DFBuyerSS(d["dfbuyer_ss"])
        self.payout_ss = PayoutSS(d["payout_ss"])
        self.web3_pp = Web3PP(d["web3_pp"], network)
        self.topup_ss = TopupSS(d["topup_ss"])  # type: ignore

        # postconditions
        self.verify_feed_dependencies()

    @staticmethod
    def constructor_dict(
        yaml_filename: Optional[str] = None,
        yaml_str: Optional[str] = None,
        nested_override_args: Optional[dict] = None,
    ) -> dict:
        # preconditions
        assert (
            yaml_filename or yaml_str and not (yaml_filename and yaml_str)
        ), "need to set yaml_filename_ or yaml_str but not both"

        # get d
        if yaml_filename is not None:
            with open(yaml_filename, "r") as f:
                d = yaml.safe_load(f)
        else:
            d = yaml.safe_load(str(yaml_str))

        if nested_override_args is not None:
            recursive_update(d, nested_override_args)

        return d

    def verify_feed_dependencies(self):
        """Raise ValueError if a feed dependency is violated"""
        lake_fs = self.lake_ss.feeds
        predict_fs = self.predictoor_ss.feeds
        aimodel_fs = self.predictoor_ss.aimodel_ss.feeds

        # is predictoor_ss.predict_feed in lake feeds?
        # - check for matching {exchange, pair, timeframe} but not {signal}
        #   because lake holds all signals o,h,l,c,v
        for predict_f in predict_fs.feeds:
            if not lake_fs.contains_combination(
                predict_f.exchange, predict_f.pair, predict_f.timeframe
            ):
                s = "predictoor_ss.predict_feed not in lake_ss.feeds"
                s += f"\n  lake_ss.feeds = {lake_fs} (ohlcv)"
                s += f"\n  predictoor_ss.predict_feed = {predict_f}"
                raise ValueError(s)

        # enforce that all predict feeds have the same timeframe
        timeframe = ""
        for predict_f in predict_fs.feeds:
            if timeframe == "":
                timeframe = predict_f.timeframe
                continue
            if predict_f.timeframe != timeframe:
                s = "predictoor_ss.predict_feed not in lake_ss.feeds"
                s += f"\n  lake_ss.feeds = {lake_fs} (ohlcv)"
                s += f"\n  predictoor_ss.predict_feed = {predict_f}"
                raise ValueError(s)

        # do all aimodel_ss input feeds conform to predict feed timeframe?
        for predict_f in predict_fs.feeds:
            for aimodel_f in aimodel_fs:
                if aimodel_f.timeframe != predict_f.timeframe:
                    s = "at least one ai_model_ss.input_feeds' timeframe incorrect"
                    s += f"\n  target={predict_f.timeframe}, in predictoor_ss.feed"
                    s += f"\n  found={aimodel_f.timeframe}, in this aimodel feed:"
                    s += f" {aimodel_f}"
                    raise ValueError(s)

        # is each predictoor_ss.aimodel_ss.input_feeds in lake feeds?
        # - check for matching {exchange, pair, timeframe} but not {signal}
        for aimodel_f in aimodel_fs:
            if not lake_fs.contains_combination(
                aimodel_f.exchange, aimodel_f.pair, aimodel_f.timeframe
            ):
                s = "at least one aimodel_ss.input_feeds not in lake_ss.feeds"
                s += f"\n  lake_ss.feeds = {lake_fs} (ohlcv)"
                s += f"\n  predictoor_ss.ai_model.input_feeds = {aimodel_fs}"
                s += f"\n  (input_feed not found: {aimodel_f})"
                raise ValueError(s)

        # is predictoor_ss.predict_feed in aimodel_ss.input_feeds?
        # - check for matching {exchange, pair, timeframe AND signal}
        for predict_f in predict_fs.feeds:
            if predict_f not in aimodel_fs:
                s = "predictoor_ss.predict_feed not in aimodel_ss.input_feeds"
                s += " (accounting for signal too)"
                s += f"\n  predictoor_ss.ai_model.input_feeds = {aimodel_fs}"
                s += f"\n  predictoor_ss.predict_feed = {predict_f}"
                raise ValueError(s)

    def __str__(self):
        s = ""
        s += f"lake_ss={self.lake_ss}\n"
        s += f"dfbuyer_ss={self.dfbuyer_ss}\n"
        s += f"payout_ss={self.payout_ss}\n"
        s += f"predictoor_ss={self.predictoor_ss}\n"
        s += f"trader_ss={self.trader_ss}\n"
        s += f"sim_ss={self.sim_ss}\n"
        s += f"trueval_ss={self.trueval_ss}\n"
        s += f"web3_pp={self.web3_pp}\n"
        return s


# =========================================================================
# utilities for testing


@enforce_types
def mock_feed_ppss(
    timeframe,
    exchange,
    pair,
    network: Optional[str] = None,
    tmpdir=None,
    pred_submitter_mgr: Optional[str] = None,
) -> Tuple[SubgraphFeed, PPSS]:
    feed = mock_feed(timeframe, exchange, pair)
    ppss = mock_ppss(
        [
            {
                "train_on": f"{exchange} {pair} c {timeframe}",
                "predict": f"{exchange} {pair} c {timeframe}",
            }
        ],
        network,
        tmpdir,
        pred_submitter_mgr=pred_submitter_mgr
    )
    return (feed, ppss)


@enforce_types
def mock_ppss(
    feeds: list,
    network: Optional[str] = None,
    tmpdir: Optional[str] = None,
    st_timestr: Optional[str] = "2023-06-18",
    fin_timestr: Optional[str] = "2023-06-21",
    pred_submitter_mgr: Optional[str] = None,
) -> PPSS:
    network = network or "development"
    yaml_str = fast_test_yaml_str(tmpdir)

    ppss = PPSS(yaml_str=yaml_str, network=network)
    predict_feeds = PredictFeeds.from_array(feeds)
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()

    assert hasattr(ppss, "lake_ss")
    ppss.lake_ss = LakeSS(
        {
            "feeds": predict_feeds.feeds_str,
            "parquet_dir": os.path.join(tmpdir, "parquet_data"),
            "st_timestr": st_timestr,
            "fin_timestr": fin_timestr,
        }
    )

    assert hasattr(ppss, "predictoor_ss")
    d = predictoor_ss_test_dict(predict_feeds=feeds, pred_submitter_mgr=pred_submitter_mgr)
    ppss.predictoor_ss = PredictoorSS(d)

    assert hasattr(ppss, "trader_ss")
    ppss.trader_ss = TraderSS(
        {
            "feed": predict_feeds.feeds_str[0],
            "sim_only": {
                "buy_amt": "10 USD",
            },
            "bot_only": {"min_buffer": 30, "max_tries": 10, "position_size": 3},
            "exchange_only": {
                "timeout": 30000,
                "options": {
                    "createMarketBuyOrderRequiresPrice": False,
                    "defaultType": "spot",
                },
            },
        }
    )

    assert hasattr(ppss, "trueval_ss")
    assert "feeds" in ppss.trueval_ss.d  # type: ignore[attr-defined]
    ppss.trueval_ss.d["feeds"] = predict_feeds.feeds_str  # type: ignore[attr-defined]

    assert hasattr(ppss, "dfbuyer_ss")
    ppss.dfbuyer_ss = DFBuyerSS(
        {
            "feeds": predict_feeds.feeds_str,
            "batch_size": 20,
            "consume_interval_seconds": 86400,
            "weekly_spending_limit": 37000,
        }
    )

    return ppss


_CACHED_YAML_FILE_S = None


@enforce_types
def fast_test_yaml_str(tmpdir=None):
    """Use this for testing. It has fast runtime."""
    global _CACHED_YAML_FILE_S
    if _CACHED_YAML_FILE_S is None:
        filename = os.path.abspath("ppss.yaml")
        with open(filename) as f:
            _CACHED_YAML_FILE_S = f.read()

    s = _CACHED_YAML_FILE_S

    if tmpdir is not None:
        assert "parquet_dir: parquet_data" in s
        s = s.replace(
            "parquet_dir: parquet_data",
            f"parquet_dir: {os.path.join(tmpdir, 'parquet_data')}",
        )

        assert "log_dir: logs" in s
        s = s.replace("log_dir: logs", f"log_dir: {os.path.join(tmpdir, 'logs')}")

    return s
