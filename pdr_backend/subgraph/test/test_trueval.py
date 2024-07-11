#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from pdr_backend.lake.trueval import Trueval, mock_truevals


@enforce_types
def test_truevals():
    truevals = mock_truevals()

    expected_column_names_types = [
        ("ID", str),
        ("truevalue", bool),
        ("timestamp", int),
        ("token", str),
        ("slot", int),
        ("revenue", float),
        ("roundSumStakesUp", float),
        ("roundSumStakes", float),
    ]

    assert truevals.shape[1] == len(expected_column_names_types), "unexpected number of columns"
    for i, (name, dtype) in enumerate(expected_column_names_types):
        assert truevals.columns[i].name == name
        assert truevals.columns[i].dtype == dtype

    assert len(truevals) == 6
    assert isinstance(truevals[0], Trueval)
    assert isinstance(truevals[1], Trueval)
    assert truevals[0].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838400"
    assert truevals[1].ID == "0x8165caab33131a4ddbf7dc79f0a8a4920b0b2553-1696838100"
