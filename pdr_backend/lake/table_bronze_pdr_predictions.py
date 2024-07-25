#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import OrderedDict
from typing import Callable

from polars import Boolean, Float64, Int64, Utf8

from pdr_backend.lake.duckdb_data_store import DuckDBDataStore
from pdr_backend.lake.lake_mapper import LakeMapper
from pdr_backend.lake.table import Table, TempTable
from pdr_backend.util.time_types import UnixTimeMs

logger = logging.getLogger("lake")


# CLEAN & ENRICHED PREDICTOOR PREDICTIONS SCHEMA
class BronzePrediction(LakeMapper):
    def __init__(self):
        super().__init__()
        self.check_against_schema()

    @staticmethod
    def get_lake_schema():
        return OrderedDict(
            {
                "ID": Utf8,  # f"{contract}-{slot}-{user}"
                "slot_id": Utf8,  # f"{contract}-{slot}"
                "contract": Utf8,  # f"{contract}"
                "slot": Int64,
                "user": Utf8,
                "pair": Utf8,
                "timeframe": Utf8,
                "source": Utf8,
                "predvalue": Boolean,
                "truevalue": Boolean,
                "stake": Float64,
                "revenue": Float64,
                "payout": Float64,
                "timestamp": Int64,
                "last_event_timestamp": Int64,
            }
        )

    @staticmethod
    def get_lake_table_name():
        return "bronze_pdr_predictions"

    @staticmethod
    def get_fetch_function() -> Callable:
        raise NotImplementedError("BronzePrediction does not have a fetch function")
