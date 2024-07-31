# pylint: disable=line-too-long
#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import OrderedDict
from typing import Callable

from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.lake_mapper import LakeMapper

logger = logging.getLogger("lake")


# CLEAN & ENRICHED PREDICTOOR SLOTS SCHEMA
class BronzeSlot(LakeMapper):
    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,  # f"{contract}-{slot}"
                "contract": Utf8,  # f"{contract}"
                "pair": Utf8,
                "timeframe": Utf8,
                "source": Utf8,
                "slot": Int64,
                "roundSumStakesUp": Float64,
                "roundSumStakes": Float64,
                "truevalue": Boolean,
                "timestamp": Int64,
                "last_event_timestamp": Int64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "bronze_pdr_slots"

    @staticmethod
    def get_fetch_function() -> Callable:
        raise NotImplementedError("BronzeSlot does not have a fetch function")
