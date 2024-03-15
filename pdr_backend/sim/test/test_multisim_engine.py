import os
from unittest import mock

from enforce_typing import enforce_types

from pdr_backend.ppss.lake_ss import LakeSS, lake_ss_test_dict
from pdr_backend.ppss.multisim_ss import MultisimSS, multisim_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import PredictoorSS, predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import SimSS, sim_ss_test_dict
from pdr_backend.sim.multisim_engine import MultisimEngine
from pdr_backend.sim.sim_state import SimState


@enforce_types
def test_multisim1(tmpdir):
    constructor_d = _constructor_d_with_fast_runtime(tmpdir)

    d = multisim_ss_test_dict(
        sweep_params=[{"predictoor_ss.aimodel_ss.autoregressive_n": "1, 2"}],
    )
    constructor_d["multisim_ss"] = d

    # go
    multisim_engine = MultisimEngine(constructor_d)
    multisim_engine.run()

    # csv ok?
    target_columns = SimState.recent_metrics_names()
    assert os.path.exists(multisim_engine.csv_file)
    df = multisim_engine.load_csv()
    assert df.shape[0] == 2 # 2 runs
    assert df.shape[1] == len(target_columns)
    assert list(df.columns) == target_columns

@enforce_types
def _constructor_d_with_fast_runtime(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    constructor_d = PPSS.constructor_dict(yaml_str=s)

    # Predictoor ss
    predict_feed = "binanceus BTC/USDT c 5m"
    input_feeds = [predict_feed]
    d = predictoor_ss_test_dict(predict_feed, input_feeds)
    d["aimodel_ss"]["max_n_train"] = 100
    constructor_d["predictoor_ss"] = d

    # lake ss
    parquet_dir = os.path.join(tmpdir, "parquet_data")
    d = lake_ss_test_dict(parquet_dir, input_feeds)
    d["st_timestr"] = "2023-06-18"
    d["fin_timestr"] = "2023-06-19"
    constructor_d["lake_ss"] = d

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    d = sim_ss_test_dict(log_dir)
    d["do_plot"] = False
    d["test_n"] = 10
    constructor_d["sim_ss"] = d

    return constructor_d
