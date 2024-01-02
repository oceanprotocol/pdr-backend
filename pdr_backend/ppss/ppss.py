import os
import tempfile
from typing import List, Optional, Tuple

import yaml
from enforce_typing import enforce_types

from pdr_backend.ppss.dfbuyer_ss import DFBuyerSS
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.payout_ss import PayoutSS
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.publisher_ss import PublisherSS
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.ppss.trader_ss import TraderSS
from pdr_backend.ppss.trueval_ss import TruevalSS
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed, mock_feed


@enforce_types
class PPSS:  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        yaml_filename: Optional[str] = None,
        yaml_str: Optional[str] = None,
        network: Optional[str] = None,  # eg "development", "sapphire-testnet"
    ):
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

        # fill attributes from d
        self.lake_ss = LakeSS(d["lake_ss"])
        self.dfbuyer_ss = DFBuyerSS(d["dfbuyer_ss"])
        self.predictoor_ss = PredictoorSS(d["predictoor_ss"])
        self.payout_ss = PayoutSS(d["payout_ss"])
        self.sim_ss = SimSS(d["sim_ss"])
        self.trader_ss = TraderSS(d["trader_ss"])
        self.trueval_ss = TruevalSS(d["trueval_ss"])
        self.publisher_ss = PublisherSS(network, d["publisher_ss"])
        self.web3_pp = Web3PP(d["web3_pp"], network)

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
_CACHED_YAML_FILE_S = None


@enforce_types
def mock_feed_ppss(
    timeframe,
    exchange,
    pair,
    network: Optional[str] = None,
    tmpdir=None,
) -> Tuple[SubgraphFeed, PPSS]:
    feed = mock_feed(timeframe, exchange, pair)
    ppss = mock_ppss([f"{exchange} {pair} c {timeframe}"], network, tmpdir)
    return (feed, ppss)


@enforce_types
def mock_ppss(
    predict_feeds: List[str],
    network: Optional[str] = None,
    tmpdir: Optional[str] = None,
    st_timestr: Optional[str] = "2023-06-18",
    fin_timestr: Optional[str] = "2023-06-21",
) -> PPSS:
    network = network or "development"
    yaml_str = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=yaml_str, network=network)

    assert hasattr(ppss, "lake_ss")
    assert hasattr(ppss, "predictoor_ss")

    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()

    ppss.lake_ss = LakeSS(
        {
            "feeds": predict_feeds,
            "parquet_dir": os.path.join(tmpdir, "parquet_data"),
            "st_timestr": st_timestr,
            "fin_timestr": fin_timestr,
        }
    )

    ppss.predictoor_ss = PredictoorSS(
        {
            "predict_feed": predict_feeds[0],
            "bot_only": {"s_until_epoch_end": 60, "stake_amount": 1},
            "aimodel_ss": {
                "input_feeds": predict_feeds,
                "approach": "LIN",
                "max_n_train": 7,
                "autoregressive_n": 3,
            },
        }
    )

    ppss.trader_ss = TraderSS(
        {
            "predict_feed": predict_feeds[0],
            "sim_only": {
                "buy_amt": "10 USD",
            },
            "bot_only": {"min_buffer": 30, "max_tries": 10, "position_size": 3},
        }
    )

    return ppss


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
