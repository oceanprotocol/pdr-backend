#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from pdr_backend.lake.payout import Payout, mock_payouts

# pylint: disable=line-too-long
@enforce_types
def test_payouts():
    payouts = mock_payouts()

    expected_column_names_types = [
        ("ID", str),
        ("token", str),
        ("user", str),
        ("slot", int),
        ("timestamp", int),
        ("payout", float),
        ("predvalue", bool),
        ("stake", float),
    ]

    assert payouts.shape[1] == len(expected_column_names_types), "unexpected number of columns"
    for i, (name, dtype) in enumerate(expected_column_names_types):
        assert payouts.columns[i].name == name
        assert payouts.columns[i].dtype == dtype

    assert len(payouts) == 6
    assert isinstance(payouts[0], Payout)
    assert isinstance(payouts[1], Payout)
    assert payouts[0].ID == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f"
    assert payouts[1].ID == "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xfb223c3583aa934273173a55c226d598a149441c"
