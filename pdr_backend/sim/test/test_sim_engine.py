import os
from unittest import mock

from enforce_typing import enforce_types

from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
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
    parquet_dir = os.path.join(tmpdir, "parquet_data")
    d = lake_ss_test_dict(parquet_dir, input_feeds)
    ppss.lake_ss = LakeSS(d)

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, final_img_filebase="final")
    ppss.sim_ss = SimSS(d)

    # go
    with mock.patch("pdr_backend.sim.sim_plotter.plt.show"):
        sim_engine = SimEngine(ppss)
        sim_engine.run()

    #
    target_name = os.path.join(log_dir, "final_0.png")
    assert os.path.exists(final_img_filename)
