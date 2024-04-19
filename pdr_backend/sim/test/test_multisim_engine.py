import os

from enforce_typing import enforce_types

from pdr_backend.ppss.lake_ss import lake_ss_test_dict
from pdr_backend.ppss.multisim_ss import multisim_ss_test_dict
from pdr_backend.ppss.ppss import PPSS, fast_test_yaml_str
from pdr_backend.ppss.predictoor_ss import predictoor_ss_test_dict
from pdr_backend.ppss.sim_ss import sim_ss_test_dict
from pdr_backend.sim.multisim_engine import MultisimEngine
from pdr_backend.sim.sim_state import SimState


@enforce_types
def test_multisim1(tmpdir):
    constructor_d = _constructor_d_with_fast_runtime(tmpdir)

    param = "predictoor_ss.aimodel_ss.autoregressive_n"
    d = multisim_ss_test_dict(sweep_params=[{param: "1, 2"}])
    constructor_d["multisim_ss"] = d

    # go
    multisim_engine = MultisimEngine(constructor_d)
    multisim_engine.run()

    # csv ok?
    target_columns = ["run_number"] + SimState.recent_metrics_names() + [param]
    assert multisim_engine.csv_header() == target_columns
    assert os.path.exists(multisim_engine.csv_file)
    df = multisim_engine.load_csv()
    assert df.shape[0] == 2  # 2 runs
    assert df.shape[1] == len(target_columns)
    assert list(df.columns) == target_columns


@enforce_types
def _constructor_d_with_fast_runtime(tmpdir):
    s = fast_test_yaml_str(tmpdir)
    main_d = PPSS.constructor_dict(yaml_str=s)

    feed_s = "binanceus BTC/USDT c 5m"
    input_feeds = [feed_s]
    feedset_list = [{"train_on": feed_s, "predict": feed_s}]

    # lake ss
    parquet_dir = os.path.join(tmpdir, "parquet_data")
    lake_d = lake_ss_test_dict(parquet_dir, input_feeds)
    assert "st_timestr" in lake_d
    assert "fin_timestr" in lake_d
    lake_d["st_timestr"] = "2023-06-18"
    lake_d["fin_timestr"] = "2023-06-19"
    assert "lake_ss" in main_d
    main_d["lake_ss"] = lake_d

    # predictoor ss
    pdr_d = predictoor_ss_test_dict(feedset_list)
    assert "aimodel_ss" in pdr_d
    assert "max_n_train" in pdr_d["aimodel_ss"]
    pdr_d["aimodel_ss"]["max_n_train"] = 100
    assert "predictoor_ss" in main_d
    main_d["predictoor_ss"] = pdr_d

    # sim ss
    log_dir = os.path.join(tmpdir, "logs")
    sim_d = sim_ss_test_dict(log_dir=log_dir, test_n=10)
    assert "sim_ss" in main_d
    main_d["sim_ss"] = sim_d

    return main_d
