#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.lake.slot import Slot
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.util.time_types import UnixTimeS


@enforce_types
def get_predict_slots_query(
    asset_ids: List[str],
    initial_slot: UnixTimeS,
    last_slot: UnixTimeS,
    first: int,
    skip: int,
) -> str:
    """
    Constructs a GraphQL query string to fetch prediction slot data for
    specified assets within a slot range.

    Args:
        asset_ids: A list of asset identifiers to include in the query.
        initial_slot: The starting slot number for the query range.
        last_slot: The ending slot number for the query range.
        first: The number of records to fetch per query (pagination limit).
        skip: The number of records to skip (pagination offset).

    Returns:
        A string representing the GraphQL query.
    """
    asset_ids_str = str(asset_ids).replace("[", "[").replace("]", "]").replace("'", '"')

    return """
        query {
            predictSlots (
            first: %s
            skip: %s
            where: {
                slot_lte: %s
                slot_gte: %s
                predictContract_in: %s
            },
            orderBy: slot,
            orderDirection: asc
            ) {
            id
            slot
            trueValues {
                id
                timestamp
                trueValue
            }
            roundSumStakesUp
            roundSumStakes
            }
        }
    """ % (
        first,
        skip,
        initial_slot,
        last_slot,
        asset_ids_str,
    )


@enforce_types
def get_slots(
    addresses: List[str],
    end_ts_param: UnixTimeS,
    start_ts_param: UnixTimeS,
    first: int,
    skip: int,
    slots: List[Slot],
    network: str = "mainnet",
) -> List[Slot]:
    """
    Retrieves slots information for given addresses and a specified time range from a subgraph.

    Args:
        addresses: A list of contract addresses to query.
        end_ts_param: The Unix timestamp representing the end of the time range.
        start_ts_param: The Unix timestamp representing the start of the time range.
        skip: The number of records to skip for pagination.
        slots: An existing list of slots to which new data will be appended.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A list of Slot TypedDicts with the queried slot information.
    """

    slots = slots or []

    query = get_predict_slots_query(
        addresses,
        end_ts_param,
        start_ts_param,
        first,
        skip,
    )

    result = query_subgraph(
        get_subgraph_url(network),
        query,
        timeout=20.0,
    )

    new_slots = result["data"]["predictSlots"] or []

    # Convert the list of dicts to a list of Slot objects
    # by passing the dict as keyword arguments
    # convert roundSumStakesUp and roundSumStakes to float
    new_slots = [
        Slot(
            **{
                "ID": slot["id"],
                "timestamp": slot["slot"],
                "slot": slot["slot"],
                "truevalue": (
                    slot["trueValues"][0]["trueValue"]
                    if "trueValues" in slot
                    and slot["trueValues"] is not None
                    and len(slot["trueValues"]) > 0
                    else None
                ),
                "roundSumStakesUp": float(slot["roundSumStakesUp"]),
                "roundSumStakes": float(slot["roundSumStakes"]),
            }
        )
        for slot in new_slots
    ]

    slots.extend(new_slots)
    return slots


@enforce_types
def fetch_slots(
    start_ts_param: UnixTimeS,
    end_ts_param: UnixTimeS,
    contracts: List[str],
    first: int,
    skip: int,
    network: str = "mainnet",
) -> Dict[str, List[Slot]]:
    """
    Fetches slots for all provided asset IDs within a given time range and organizes them by asset.

    Args:
        contracts: A list of asset identifiers for which slots will be fetched.
        start_ts_param: The Unix timestamp marking the beginning of the desired time range.
        end_ts_param: The Unix timestamp marking the end of the desired time range.
        network: The blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dictionary mapping asset IDs to lists of Slot dataclass
        containing slot information.
    """

    all_slots = get_slots(
        contracts, end_ts_param, start_ts_param, first, skip, [], network
    )
    return all_slots
