from typing import List
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.subgraph.payout import Payout

@enforce_types
def get_payout_query(
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
            predictPayouts (
            first: %s
            skip: %s
            where: { slot_: {slot_gte: %s, slot_lte: %s, predictContract_in: %s}}
            ) {
            id
            timestamp
            payout
            prediction {
                user {
                    id
                }
            }
            slot {
                id
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
