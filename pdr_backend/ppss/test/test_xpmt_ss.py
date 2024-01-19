import copy
import os
import pytest

from enforce_typing import enforce_types

from pdr_backend.ppss.xpmt_ss import XpmtSS

_D = {"do_plot": False, "log_dir": "logs", "test_n": 2}


@enforce_types
def test_xpmt_ss():
    ss = XpmtSS(_D)

    # yaml properties
    assert not ss.do_plot
    assert "logs" in ss.log_dir
    assert ss.test_n == 2

    # str
    assert "XpmtSS" in str(ss)


@enforce_types
def test_xpmt_ss_bad():
    bad = copy.deepcopy(_D)
    bad["test_n"] = -3

    with pytest.raises(ValueError):
        XpmtSS(bad)

    bad = copy.deepcopy(_D)
    bad["test_n"] = "lit"

    with pytest.raises(ValueError):
        XpmtSS(bad)


@enforce_types
def test_log_dir(tmpdir):
    # rel path given; needs an abs path
    d = copy.deepcopy(_D)
    d["log_dir"] = "logs"
    ss = XpmtSS(d)
    target_log_dir = os.path.abspath("logs")
    assert ss.log_dir == target_log_dir

    # abs path given
    d = copy.deepcopy(_D)
    d["log_dir"] = os.path.join(tmpdir, "logs")
    ss = XpmtSS(d)
    target_log_dir = os.path.join(tmpdir, "logs")
    assert ss.log_dir == target_log_dir
