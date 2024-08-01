#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import OrderedDict
from typing import Callable, List

from enforce_typing import enforce_types
from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
class Payout(LakeMapper):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        ID: str,
        token: str,
        user: str,
        slot: UnixTimeS,
        timestamp: UnixTimeS,
        payout: float,
        predvalue: bool,
        truevalue: bool,
        stake: float,
    ) -> None:
        self.ID = ID
        self.user = user
        self.timestamp = timestamp
        self.token = token
        self.slot = slot
        self.payout = payout
        self.predvalue = predvalue
        self.truevalue = truevalue
        self.stake = stake

        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,
                "token": Utf8,
                "user": Utf8,
                "slot": Int64,
                "timestamp": Int64,
                "payout": Float64,
                "predvalue": Boolean,
                "truevalue": Boolean,
                "stake": Float64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "pdr_payouts"

    @staticmethod
    def get_fetch_function() -> Callable:
        # pylint: disable=import-outside-toplevel
        from pdr_backend.subgraph.subgraph_payout import (
            fetch_payouts,
        )

        return fetch_payouts


@enforce_types
def mock_payout(payout_tuple: tuple) -> Payout:
    (
        ID,
        user,
        timestamp,
        token,
        slot,
        payout,
        predvalue,
        truevalue,
        stake,
    ) = payout_tuple

    return Payout(
        ID=ID,
        user=user,
        timestamp=UnixTimeS(timestamp),
        token=token,
        slot=UnixTimeS(slot),
        payout=payout,
        predvalue=predvalue,
        truevalue=truevalue,
        stake=stake,
    )


@enforce_types
def mock_payouts() -> List[Payout]:
    return [mock_payout(payout_tuple) for payout_tuple in _PAYOUT_TUPS]


@enforce_types
def mock_payouts_related_with_predictions() -> List[Payout]:
    return [
        mock_payout(payout_tuple)
        for payout_tuple in _PAYOUT_TUPS_RELATED_WITH_PREDICTIONS
    ]


_PAYOUT_TUPS = [
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",  # user
        1704153558,  # timestamp
        "ADA/USDT",  # token
        1704152700,  # slot
        0.0,  # payout
        True,  # predictedValue
        True,  # truevalue
        0.41,  # stake
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xfb223c3583aa934273173a55c226d598a149441c",
        "0xfb223c3583aa934273173a55c226d598a149441c",
        1704153051,
        "ADA/USDT",
        1704152700,
        3.786517720904995824,
        False,
        False,
        2.049314196396558,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        "0x02e9d2eede4c5347e55346860c8a8988117bde9e",
        1704153351,
        "ADA/USDT",
        1704153000,
        3.687473663992716148,
        False,
        False,
        1.9908170679122585,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        "0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        1704153504,
        "ADA/USDT",
        1704153000,
        6.334665366356455078,
        False,
        False,
        3.4200000000000004,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        "0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        1704153534,
        "ADA/USDT",
        1704153000,
        1.463270654801637113,
        False,
        False,
        0.79,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        1704153558,
        "ADA/USDT",
        1704153000,
        0.0,
        True,
        True,
        0.41,
    ),
]


_PAYOUT_TUPS_RELATED_WITH_PREDICTIONS = [
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",  # user
        1704153558,  # timestamp
        "ADA/USDT",  # token
        1704152700,  # slot
        1.4,  # payout
        True,  # predictedValue
        True,  # predictedValue
        0.41,  # stake
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704152700-0xfb223c3583aa934273173a55c226d598a149441c",
        "0xfb223c3583aa934273173a55c226d598a149441c",
        1704153051,
        "ADA/USDT",
        1704152700,
        3.786517720904995824,
        False,
        False,
        2.049314196396558,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        "0xd2a24cb4ff2584bad80ff5f109034a891c3d88dd",
        1704153351,
        "ADA/USDT",
        1704153000,
        3.687473663992716148,
        False,
        False,
        1.9908170679122585,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        "0x04a5e9f565dfa83c77581d1022b9ef041f55210b",
        1704153504,
        "ADA/USDT",
        1704153000,
        6.334665366356455078,
        False,
        False,
        3.4200000000000004,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        "0x7149ceca72c61991018ed80788bea3f3f4540c3c",
        1704153534,
        "ADA/USDT",
        1704153000,
        1.463270654801637113,
        False,
        False,
        0.79,
    ),
    (
        # pylint: disable=line-too-long
        "0x18f54cc21b7a2fdd011bea06bba7801b280e3151-1704153000-0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        "0xeb18bad7365a40e36a41fb8734eb0b855d13b74f",
        1704153558,
        "ADA/USDT",
        1704153000,
        0.0,
        True,
        True,
        0.41,
    ),
]
