#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import pytest

from enforce_typing import enforce_types

from pdr_backend.ppss.sim_ss import (
    SimSS,
    sim_ss_test_dict,
    TRADETYPE_OPTIONS,
)


@enforce_types
def test_sim_ss_defaults(tmpdir):
    d = sim_ss_test_dict(_logdir(tmpdir))
    ss = SimSS(d)

    # yaml properties
    assert isinstance(ss.log_dir, str)
    assert isinstance(ss.test_n, int)
    assert 1 <= ss.test_n <= 10000
    assert ss.tradetype == "histmock"

    # str
    assert "SimSS" in str(ss)


@enforce_types
def test_sim_ss_specify_values(tmpdir):
    d = sim_ss_test_dict(
        log_dir=os.path.join(tmpdir, "mylogs"),
        test_n=13,
        tradetype="livereal",
    )
    ss = SimSS(d)

    # yaml properties
    assert ss.log_dir == os.path.join(tmpdir, "mylogs")
    assert ss.test_n == 13
    assert ss.tradetype == "livereal"

    # str
    assert "SimSS" in str(ss)


@enforce_types
def test_sim_ss_log_dir_relative_path():
    # it will work with the relative path
    expanded_path = os.path.abspath("mylogs")
    had_before = os.path.exists(expanded_path)
    d = sim_ss_test_dict("mylogs")
    ss = SimSS(d)
    assert ss.log_dir == expanded_path
    if not had_before:
        os.rmdir(expanded_path)


@enforce_types
def test_sim_ss_test_n_badpaths(tmpdir):
    d = sim_ss_test_dict(_logdir(tmpdir), test_n=-3)
    with pytest.raises(ValueError):
        _ = SimSS(d)

    d = sim_ss_test_dict(_logdir(tmpdir))
    d["test_n"] = "not_an_int"
    with pytest.raises(TypeError):
        _ = SimSS(d)

    d = sim_ss_test_dict(_logdir(tmpdir))
    d["test_n"] = 3.2
    with pytest.raises(TypeError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_tradetype_happypaths(tmpdir):
    for tradetype in TRADETYPE_OPTIONS:
        d = sim_ss_test_dict(_logdir(tmpdir), tradetype=tradetype)
        ss = SimSS(d)
        assert ss.tradetype == tradetype


@enforce_types
def test_sim_ss_tradetype_badpaths(tmpdir):
    d = sim_ss_test_dict(_logdir(tmpdir))
    d["tradetype"] = 3.2
    with pytest.raises(TypeError):
        _ = SimSS(d)

    d = sim_ss_test_dict(_logdir(tmpdir), tradetype="not a tradetype")
    with pytest.raises(ValueError):
        _ = SimSS(d)


@enforce_types
def test_sim_ss_is_final_iter(tmpdir):
    d = sim_ss_test_dict(_logdir(tmpdir), test_n=10)
    ss = SimSS(d)
    with pytest.raises(ValueError):
        _ = ss.is_final_iter(-5)
    assert not ss.is_final_iter(0)
    assert ss.is_final_iter(9)
    with pytest.raises(ValueError):
        _ = ss.is_final_iter(11)


@enforce_types
def test_sim_ss_setters(tmpdir):
    d = sim_ss_test_dict(_logdir(tmpdir))
    ss = SimSS(d)

    # test_n
    ss.set_test_n(32)
    assert ss.test_n == 32
    with pytest.raises(ValueError):
        ss.set_test_n(0)
    with pytest.raises(ValueError):
        ss.set_test_n(-5)

    # tradetype
    ss.set_tradetype("livereal")
    assert ss.tradetype == "livereal"
    with pytest.raises(ValueError):
        ss.set_tradetype("foo")


# ====================================================================
# helper funcs
@enforce_types
def _logdir(tmpdir) -> str:
    return os.path.join(tmpdir, "mylogs")
