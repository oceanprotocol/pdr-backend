#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from enforce_typing import enforce_types

from pdr_backend.cli.arg_db import (
    ArgDB,
    ArgDBs,
    db_str_ok,
    verify_db_str,
    verify_dbs_str,
)


# ==========================================================================
# conversions
@enforce_types
def test_verify_db_str():
    verify_db_str("db_210.1")
    verify_db_str("db_210")

    for bad_val in ["", " ", "foo", "db", "vbab", "dbab", "db-210", "210"]:
        with pytest.raises(ValueError):
            verify_db_str(bad_val)

    for bad_val in [None, 1.1, [], ["db210"]]:
        with pytest.raises(TypeError):
            verify_db_str(bad_val)


@enforce_types
def test_verify_dbs_str():
    verify_dbs_str("db_210.1")
    verify_dbs_str("db_210")
    verify_dbs_str("db_210,db_210.4")

    for bad_val in ["", " ", "foo", "db-", "db-ab", "db210", "210", "db-2", "db_12,"]:
        with pytest.raises(ValueError):
            verify_dbs_str(bad_val)

    for bad_val in [None, 1.1, [], ["db210"]]:
        with pytest.raises(TypeError):
            verify_dbs_str(bad_val)


@enforce_types
def test_db_str_ok():
    assert db_str_ok("db_210")
    db_str_ok("db_210.1,db_210.3")

    for bad_val in ["", " ", "foo", "db-", "db_ab", "db210", "210", "db-2"]:
        assert not db_str_ok(bad_val)

    for bad_val in [None, 1.1, [], ["db210"]]:
        with pytest.raises(TypeError):
            db_str_ok(bad_val)
