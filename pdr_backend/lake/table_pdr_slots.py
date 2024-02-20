from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Float64, Int64, Utf8, Boolean

from pdr_backend.subgraph.subgraph_slot import fetch_slots
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

slots_table_name = "pdr_slots"

# RAW SLOT SCHEMA
slots_schema = {
    "ID": Utf8,
    "timestamp": Int64,
    "slot": Int64,
    "trueval": Boolean,
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
}
