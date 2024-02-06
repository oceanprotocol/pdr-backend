from typing import Dict
import polars as pl
from enforce_typing import enforce_types
from polars import Float64, Int64, Utf8, List

from pdr_backend.subgraph.subgraph_slot import fetch_slots
from pdr_backend.lake.plutil import _object_list_to_df
from pdr_backend.util.networkutil import get_sapphire_postfix
from pdr_backend.util.timeutil import ms_to_seconds

# RAW SLOT SCHEMA
slots_schema = {
    "ID": Utf8,
    "timestamp": Int64,
    "slot": Int64,
    "trueValues": List(Utf8),
    "roundSumStakesUp": Float64,
    "roundSumStakes": Float64,
}


@enforce_types
def get_pdr_slots_df(
    network: str, st_ut: int, fin_ut: int, config: Dict
) -> pl.DataFrame:
    """
    @description
        Fetch raw slots from predictoor subgraph
        Update function for graphql query, returns raw data
        + Transforms ts into ms as required for data factory
    """
    network = get_sapphire_postfix(network)

    # fetch slots
    slots = fetch_slots(
        config["contract_list"], ms_to_seconds(st_ut), ms_to_seconds(fin_ut), network
    )

    print(slots)

    if len(slots) == 0:
        print("No slots to fetch. Exit.")
        return pl.DataFrame()

    # convert slots to df, transform timestamp into ms, return in-order
    slot_df = _object_list_to_df(slots, slots_schema)

    return slot_df
