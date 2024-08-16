#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_tb import (
    ArgTB,
    ArgTBs,
    tb_str_ok,
    verify_tb_str,
    verify_tbs_str,
)


# ==========================================================================
# conversions
@enforce_types
def test_verify_vb_str():
    verify_tb_str("tb_210")

    for bad_val in ["", " ", "foo", "vb", "tbab", "tb-210.1", "210"]:
        with pytest.raises(ValueError):
            verify_tb_str(bad_val)

    for bad_val in [None, 1.1, [], ["tb210"]]:
        with pytest.raises(TypeError):
            verify_tb_str(bad_val)


@enforce_types
def test_verify_tbs_str():
    verify_tbs_str("tb_210")
    verify_tbs_str("tb_210,tb_214")

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
        "tb_12.5",
    ]:
        with pytest.raises(ValueError):
            verify_tbs_str(bad_val)

    for bad_val in [None, 1.1, [], ["vb210"]]:
        with pytest.raises(TypeError):
            verify_tbs_str(bad_val)


@enforce_types
def test_tb_str_ok():
    assert tb_str_ok("tb_210")
    tb_str_ok("tb_210,tb_210")

    for bad_val in ["", " ", "foo", "tb-", "tb_ab", "tb210", "210", "tb-2"]:
        assert not tb_str_ok(bad_val)

    for bad_val in [None, 1.1, [], ["tb210"]]:
        with pytest.raises(TypeError):
            tb_str_ok(bad_val)
