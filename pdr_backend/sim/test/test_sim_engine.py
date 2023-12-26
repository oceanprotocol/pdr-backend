import os

from enforce_typing import enforce_types

from pdr_backend.ppss.data_pp import DataPP
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.ppss.aimodel_ss import AimodelSS
from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_sim_engine(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    assert hasattr(ppss, "data_pp")
    ppss.data_pp = DataPP(
        {
            "timeframe": "5m",
            "predict_feeds": ["binanceus BTC/USDT c"],
            "sim_only": {"test_n": 10},
        }
    )
    assert hasattr(ppss, "aimodel_ss")
    ppss.aimodel_ss = AimodelSS(
        {
            "input_feeds": ["binanceus BTC/USDT ETH/USDT oc"],
            "max_n_train": 100,
            "autoregressive_n": 2,
            "approach": "LIN",
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
        }
    )

    sim_engine = SimEngine(ppss)
    sim_engine.run()
