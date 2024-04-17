import os
from enforce_typing import enforce_types
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedsets

from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_sim_engine(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    # set feeds; we'll use them below
    feedset_list = [
        {
            "predict": "binanceus BTC/USDT c 5m",
            "train_on": "binanceus BTC/USDT c 5m",
        }
    ]
    feedsets = PredictTrainFeedsets.from_array(feedset_list)
    
    # lake ss
    parquet_dir = os.path.join(tmpdir, "parquet_data")
    d = lake_ss_test_dict(parquet_dir, feeds=feedsets.feeds_str)
    assert "st_timestr" in d
    d["st_timestr"] = "2023-06-18"
    d["fin_timestr"] = "2023-06-19"
    ppss.lake_ss = LakeSS(d)

    # predictoor ss
    d = predictoor_ss_test_dict(feedset_list)
    assert "approach" in d["aimodel_ss"]
    assert "max_n_train" in d["aimodel_ss"]
    assert "autoregressive_n" in d["aimodel_ss"]
    d["aimodel_ss"]["approach"] = "LinearLogistic"
    d["aimodel_ss"]["max_n_train"] = 20
    d["aimodel_ss"]["autoregressive_n"] = 1
    ppss.predictoor_ss = PredictoorSS(d)

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, test_n=5)
    ppss.sim_ss = SimSS(d)

    # go
    feedsets = ppss.predictoor_ss.predict_train_feedsets
    sim_engine = SimEngine(ppss, feedsets[0])
    sim_engine.run()

    # after implementing the P/C architeture, check state saved
