import os

from dash import Dash
from enforce_typing import enforce_types

from pdr_backend.aimodel.aimodel import Aimodel
from pdr_backend.cli.predict_train_feedsets import PredictTrainFeedsets
from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.dash_plots.callbacks import get_callbacks
from pdr_backend.sim.dash_plots.view_elements import get_layout
from pdr_backend.sim.sim_engine import SimEngine


@enforce_types
def test_sim_engine(tmpdir, dash_duo):
    s = fast_test_yaml_str(tmpdir)
    ppss = PPSS(yaml_str=s, network="development")

    # set feeds; we'll use them below
    feedset_list = [
        {
            "predict": "binanceus BTC/USDT c 5m",
            "train_on": "binanceus BTC/USDT c 5m",
        }
    ]
    feedsets = PredictTrainFeedsets.from_list_of_dict(feedset_list)

    # lake ss
    parquet_dir = os.path.join(tmpdir, "parquet_data")
    d = lake_ss_test_dict(parquet_dir, feeds=feedsets.feed_strs)
    assert "st_timestr" in d
    d["st_timestr"] = "2023-06-18"
    d["fin_timestr"] = "2023-06-19"
    ppss.lake_ss = LakeSS(d)

    # predictoor ss
    d = predictoor_ss_test_dict(feedset_list)
    assert "max_n_train" in d["aimodel_data_ss"]
    assert "autoregressive_n" in d["aimodel_data_ss"]
    assert "approach" in d["aimodel_ss"]
    assert "train_every_n_epochs" in d["aimodel_ss"]
    d["aimodel_data_ss"]["max_n_train"] = 20
    d["aimodel_data_ss"]["autoregressive_n"] = 1
    d["aimodel_ss"]["approach"] = "ClassifLinearRidge"
    d["aimodel_ss"]["train_every_n_epochs"] = 2
    ppss.predictoor_ss = PredictoorSS(d)

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir, test_n=5)
    ppss.sim_ss = SimSS(d)

    # go
    feedsets = ppss.predictoor_ss.predict_train_feedsets
    sim_engine = SimEngine(ppss, feedsets[0])

    assert sim_engine.crt_trained_model is None
    sim_engine.run()
    assert isinstance(sim_engine.crt_trained_model, Aimodel)

    app = Dash("pdr_backend.sim.sim_dash")
    app.config["suppress_callback_exceptions"] = True
    app.run_id = sim_engine.multi_id
    app.layout = get_layout()
    get_callbacks(app)

    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal(
        "#sim_state_text", f"Simulation ID: {sim_engine.multi_id}", timeout=100
    )
