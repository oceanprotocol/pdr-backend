import os

from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_sim_engine(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    ppss.predictoor_ss = PredictoorSS(
        {
            "predict_feed": "binanceus BTC/USDT c",
            "timeframe": "5m",
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
            "feeds": ["binanceus BTC/USDT ETH/USDT oc"],
            "parquet_dir": os.path.join(tmpdir, "parquet_data"),
            "st_timestr": "2023-06-18",
            "fin_timestr": "2023-06-30",
        }
    )

    assert hasattr(ppss, "sim_ss")
    ppss.sim_ss = SimSS(
        {
            "do_plot": False,
            "log_dir": os.path.join(tmpdir, "logs"),
            "test_n": 10,
        }
    )

    sim_engine = SimEngine(ppss)
    sim_engine.run()
