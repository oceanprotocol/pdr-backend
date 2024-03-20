import os
from pathlib import Path
import pytest

from enforce_typing import enforce_types

from pdr_backend.ppss.sim_ss import (
    SimSS,
    sim_ss_test_dict,
    TRADETYPE_OPTIONS,
)


@enforce_types
def test_sim_ss_defaults(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir))
    ss = SimSS(d)

    # yaml properties
    assert isinstance(ss.do_plot, bool)
    assert isinstance(ss.log_dir, str)
    assert isinstance(ss.test_n, int)
    assert 1 <= ss.test_n <= 10000
    assert "png" in ss.unique_final_img_filename()
    assert ss.tradetype == "histmock"

    # str
    assert "SimSS" in str(ss)


@enforce_types
def test_sim_ss_give_values(tmpdir):
    d = sim_ss_test_dict(
        do_plot=False,
        log_dir=os.path.join(tmpdir, "mylogs"),
        final_img_filebase="foo_final_img",
        test_n=13,
        tradetype="livereal",
    )
    ss = SimSS(d)

    # yaml properties
    assert not ss.do_plot
    assert ss.log_dir == os.path.join(tmpdir, "mylogs")
    assert ss.final_img_filebase == "foo_final_img"
    assert "foo_final_img" in ss.unique_final_img_filename()
    assert "png" in ss.unique_final_img_filename()
    assert ss.test_n == 13
    assert ss.tradetype == "livereal"

    # str
    assert "SimSS" in str(ss)


@enforce_types
def test_sim_ss_do_plot_badpaths(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir))
    d["do_plot"] = "not_a_bool"
    with pytest.raises(TypeError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_log_dir_relative_path():
    # it will work with the relative path
    expanded_path = os.path.abspath("mylogs")
    had_before = os.path.exists(expanded_path)
    d = sim_ss_test_dict(True, "mylogs")
    ss = SimSS(d)
    assert ss.log_dir == expanded_path
    if not had_before:
        os.rmdir(expanded_path)


@enforce_types
def test_sim_ss_final_img_filebase_badpaths(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir))
    d["final_img_filebase"] = 3.2  # not a str
    with pytest.raises(TypeError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_test_n_badpaths(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir), test_n=-3)
    with pytest.raises(ValueError):
        _ = SimSS(d)

    d = sim_ss_test_dict(True, _logdir(tmpdir))
    d["test_n"] = "not_an_int"
    with pytest.raises(TypeError):
        _ = SimSS(d)

    d = sim_ss_test_dict(True, _logdir(tmpdir))
    d["test_n"] = 3.2
    with pytest.raises(TypeError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_tradetype_happypaths(tmpdir):
    for tradetype in TRADETYPE_OPTIONS:
        d = sim_ss_test_dict(True, _logdir(tmpdir), tradetype=tradetype)
        ss = SimSS(d)
        assert ss.tradetype == tradetype


@enforce_types
def test_sim_ss_tradetype_badpaths(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir))
    d["tradetype"] = 3.2
    with pytest.raises(TypeError):
        _ = SimSS(d)

    d = sim_ss_test_dict(True, _logdir(tmpdir), tradetype="not a tradetype")
    with pytest.raises(ValueError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_is_final_iter(tmpdir):
    d = sim_ss_test_dict(True, _logdir(tmpdir), test_n=10)
    ss = SimSS(d)
    with pytest.raises(ValueError):
        _ = ss.is_final_iter(-5)
    assert not ss.is_final_iter(0)
    assert ss.is_final_iter(9)
    with pytest.raises(ValueError):
        _ = ss.is_final_iter(11)


@enforce_types
def test_sim_ss_unique_final_img_filename(tmpdir):
    log_dir = os.path.join(str(tmpdir), "logs")
    d = sim_ss_test_dict(True, log_dir, final_img_filebase="final")
    ss = SimSS(d)

    target_name0 = os.path.join(log_dir, "final_0.png")
    assert ss.unique_final_img_filename() == target_name0
    assert ss.unique_final_img_filename() == target_name0  # call 2x, get same

    Path(target_name0).touch()

    target_name1 = os.path.join(log_dir, "final_1.png")
    assert ss.unique_final_img_filename() == target_name1

    Path(target_name1).touch()

    target_name2 = os.path.join(log_dir, "final_2.png")
    assert ss.unique_final_img_filename() == target_name2


# ====================================================================
# helper funcs
@enforce_types
def _logdir(tmpdir) -> str:
    return os.path.join(tmpdir, "mylogs")
