#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from polars import Boolean, Int64, Utf8

truevals_table_name = "pdr_truevals"

# RAW TRUEVAL SCHEMA
truevals_schema = {
    "ID": Utf8,
    "token": Utf8,
    "timestamp": Int64,
    "trueval": Boolean,
    "slot": Int64,
}
