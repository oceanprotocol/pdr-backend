import os
from unittest import mock

from enforce_typing import enforce_types

from pdr_backend.ppss.lake_ss import LakeSS
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_sim_engine(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    # predictoor ss
    predict_feed = "binanceus BTC/USDT c 5m"
    input_feeds = ["binanceus BTC/USDT ETH/USDT oc 5m"]
    d = predictoor_ss_test_dict(predict_feed, input_feeds)
    d["aimodel_ss"]["approach"] = "LinearLogistic"
    d["aimodel_ss"]["max_n_train"] = 100
    d["aimodel_ss"]["autoregressive_n"] = 3
    ppss.predictoor_ss = PredictoorSS(d)

    # lake ss
    d = {
        "feeds": input_feeds,
        "parquet_dir": os.path.join(tmpdir, "parquet_data"),
        "st_timestr": "2023-06-18",
        "fin_timestr": "2023-06-30",
        "timeframe": "5m",
    }
    ppss.lake_ss = LakeSS(d)

    # sim ss
    d = {
        "do_plot": True,
        "log_dir": os.path.join(tmpdir, "logs"),
        "test_n": 10,
        "exchange_only": {
            "timeout": 30000,
            "options": {
                "createMarketBuyOrderRequiresPrice": False,
                "defaultType": "spot",
            },
        },
    }
    ppss.sim_ss = SimSS(d)

    # go
    with mock.patch("pdr_backend.sim.sim_plotter.plt.show"):
        sim_engine = SimEngine(ppss)
        sim_engine.run()
