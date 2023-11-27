import copy
import os

from enforce_typing import enforce_types

from pdr_backend.ppss.sim_ss import SimSS

_D = {"do_plot": False, "log_dir": "logs"}


@enforce_types
def test_sim_ss():
    ss = SimSS(_D)

    # yaml properties
    assert not ss.do_plot
    assert "logs" in ss.log_dir

    # str
    assert "SimSS" in str(ss)


@enforce_types
def test_log_dir(tmpdir):
    # rel path given; needs an abs path
    d = copy.deepcopy(_D)
    d["log_dir"] = "logs"
    ss = SimSS(d)
    target_log_dir = os.path.abspath("logs")
    assert ss.log_dir == target_log_dir

    # abs path given
    d = copy.deepcopy(_D)
    d["log_dir"] = os.path.join(tmpdir, "logs")
    ss = SimSS(d)
    target_log_dir = os.path.join(tmpdir, "logs")
    assert ss.log_dir == target_log_dir
