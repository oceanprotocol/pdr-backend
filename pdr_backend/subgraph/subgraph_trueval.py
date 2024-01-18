from typing import List
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.subgraph.trueval import Trueval


@enforce_types
def get_truevals_query(
    asset_ids: List[str], start_ts: int, end_ts: int, first: int, skip: int
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
            predictTrueVals (
            first: %s
            skip: %s
            where: { timestamp_gte: %s, timestamp_lte: %s, slot_: {predictContract_in: %s}}
            ) {
            id
            timestamp
            trueValue
            slot {
                id
                predictContract{
                    token{
                        name
                    }
                }
            }
            }
        }
    """ % (
        first,
        skip,
        start_ts,
        end_ts,
        asset_ids_str,
    )


@enforce_types
def fetch_truevals(
    addresses: List[str],
    start_ts: int,
    end_ts: int,
    skip: int,
    network: str = "mainnet",
) -> List[Trueval]:
    records_per_page = 10
    query = get_truevals_query(
        addresses,
        start_ts,
        end_ts,
        records_per_page,
        skip,
    )

    result = query_subgraph(
        get_subgraph_url(network),
        query,
        timeout=20.0,
    )

    print(result)
    new_truevals = result["data"]["predictTrueVals"] or []

    new_truevals = [
        Trueval(
            **{
                "trueval": trueval["trueValue"],
                "timestamp": trueval["timestamp"],
                "ID": trueval["id"],
                "token": trueval["slot"]["predictContract"]["token"]["name"],
                "slot": int(trueval["id"].split("-")[1]),
            }
        )
        for trueval in new_truevals
    ]
    return new_truevals
