#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_vb import (
    ArgVB,
    ArgVBs,
    vb_str_ok,
    verify_vb_str,
    verify_vbs_str,
)


# ==========================================================================
# conversions
@enforce_types
def test_verify_vb_str():
    verify_vb_str("vb_210.1")
    verify_vb_str("vb_210")

    for bad_val in ["", " ", "foo", "vb", "vbab", "vb-210", "210"]:
        with pytest.raises(ValueError):
            verify_vb_str(bad_val)

    for bad_val in [None, 1.1, [], ["vb210"]]:
        with pytest.raises(TypeError):
            verify_vb_str(bad_val)


@enforce_types
def test_verify_vbs_str():
    verify_vbs_str("vb_210.1")
    verify_vbs_str("vb_210")
    verify_vbs_str("vb_210,vb_210.4")

    for bad_val in ["", " ", "foo", "vb-", "vb-ab", "vb210", "210", "vb-2", "vb_12,"]:
        with pytest.raises(ValueError):
            verify_vbs_str(bad_val)

    for bad_val in [None, 1.1, [], ["vb210"]]:
        with pytest.raises(TypeError):
            verify_vbs_str(bad_val)


@enforce_types
def test_vb_str_ok():
    assert vb_str_ok("vb_210")
    vb_str_ok("vb_210.1,vb_210.3")

    for bad_val in ["", " ", "foo", "vb-", "vb_ab", "vb210", "210", "vb-2"]:
        assert not vb_str_ok(bad_val)

    for bad_val in [None, 1.1, [], ["vb210"]]:
        with pytest.raises(TypeError):
            vb_str_ok(bad_val)
