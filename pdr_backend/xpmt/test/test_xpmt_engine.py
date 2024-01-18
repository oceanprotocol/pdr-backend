import os
from unittest import mock

from enforce_typing import enforce_types

from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.xpmt_ss import XpmtSS
from pdr_backend.xpmt.xpmt_engine import XpmtEngine


@enforce_types
def test_xpmt_engine(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    ppss.predictoor_ss = PredictoorSS(
        {
            "predict_feed": "binanceus BTC/USDT c 5m",
            "bot_only": {"s_until_epoch_end": 60, "stake_amount": 1},
            "aimodel_ss": {
                "input_feeds": ["binanceus BTC/USDT ETH/USDT oc"],
                "max_n_train": 100,
                "autoregressive_n": 2,
                "approach": "LIN",
            },
        }
    )

    ppss.lake_ss = LakeSS(
        {
            "feeds": ["binanceus BTC/USDT ETH/USDT oc 5m"],
            "parquet_dir": os.path.join(tmpdir, "parquet_data"),
            "st_timestr": "2023-06-18",
            "fin_timestr": "2023-06-30",
            "timeframe": "5m",
        }
    )

    assert hasattr(ppss, "xpmt_ss")
    ppss.xpmt_ss = XpmtSS(
        {
            "do_plot": True,
            "log_dir": os.path.join(tmpdir, "logs"),
            "test_n": 10,
        }
    )

    with mock.patch("pdr_backend.xpmt.xpmt_engine.plt.show"):
        xpmt_engine = XpmtEngine(ppss)
        xpmt_engine.run()
