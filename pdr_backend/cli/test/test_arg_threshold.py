#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_threshold import (
    ArgThreshold,
    threshold_str_ok,
    verify_threshold_str,
    verify_thresholds_str,
)


# ==========================================================================
# conversions
@enforce_types
def test_argThreshold_to_str():
    arg_t = ArgThreshold("db_210.5")
    assert str(arg_t) == "db_210.5"


@enforce_types
def test_verify_threshold_str():
    verify_threshold_str("tb_210")
    verify_threshold_str("db_210.5")
    verify_threshold_str("vb_210")

    for bad_val in ["", " ", "foo", "vb", "tbab", "tb-210.1", "210", "pb_2015", 'vb_ab']:
        with pytest.raises(ValueError):
            verify_threshold_str(bad_val)

    for bad_val in [None, 1.1, [], ["tb210"]]:
        with pytest.raises(TypeError):
            verify_threshold_str(bad_val)


@enforce_types
def test_verify_thresholds_str():
    verify_thresholds_str("tb_210")
    verify_thresholds_str("tb_210.5,tb_214")

    for bad_val in [
        "",
        " ",
        "foo",
        "tb-",
        "tb-ab",
        "tb210",
        "210",
        "tb-2",
        "tb_12,",
    ]:
        with pytest.raises(ValueError):
            verify_thresholds_str(bad_val)

    for bad_val in [None, 1.1, [], ["vb210"]]:
        with pytest.raises(TypeError):
            verify_thresholds_str(bad_val)


@enforce_types
def test_tb_str_ok():
    assert threshold_str_ok("tb_210")
    threshold_str_ok("tb_210,tb_210")

    for bad_val in ["", " ", "foo", "tb-", "tb210", "210", "tb-2"]:
        assert not threshold_str_ok(bad_val)

    for bad_val in [None, 1.1, [], ["tb210"]]:
        with pytest.raises(TypeError):
            threshold_str_ok(bad_val)
