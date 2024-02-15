import logging
from typing import List
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.subgraph.trueval import Trueval

logger = logging.getLogger("subgraph")


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
    start_ts: int,
    end_ts: int,
    addresses: List[str],
    network: str = "mainnet",
) -> List[Trueval]:
    """
    @description
        Implements same pattern as fetch_filtered_predictions
    """

    chunk_size = 1000
    offset = 0
    truevals: List[Trueval] = []

    while True:
        query = get_truevals_query(
            addresses,
            start_ts,
            end_ts,
            chunk_size,
            offset,
        )

        try:
            logger.info("Querying subgraph... %s", query)
            result = query_subgraph(
                get_subgraph_url(network),
                query,
                timeout=20.0,
            )
        except Exception as e:
            logger.warning(
                "Error fetching predictTrueVals, got #%d items. Exception: %s",
                len(truevals),
                e,
            )
            break

        offset += chunk_size

        if "data" not in result or not result["data"]:
            break

        data = result["data"].get("predictTrueVals", [])
        if len(data) == 0:
            break

        for record in data:
            truevalue = record["trueValue"]
            timestamp = record["timestamp"]
            ID = record["id"]
            token = record["slot"]["predictContract"]["token"]["name"]
            slot = int(record["id"].split("-")[1])

            trueval = Trueval(
                ID=ID,
                token=token,
                timestamp=timestamp,
                trueval=truevalue,
                slot=slot,
            )

            truevals.append(trueval)

        # avoids doing next fetch if we've reached the end
        if len(data) < chunk_size:
            break

    return truevals
