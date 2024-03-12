from typing import List
import logging
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.subgraph.trueval import Trueval
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("trueval")


@enforce_types
def get_truevals_query(
    asset_ids: List[str],
    start_ts: UnixTimeS,
    end_ts: UnixTimeS,
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
    start_ts: UnixTimeS,
    end_ts: UnixTimeS,
    addresses: List[str],
    first: int,
    skip: int,
    network: str = "mainnet",
) -> List[Trueval]:
    """
    @description
        Implements same pattern as fetch_filtered_predictions
    """
    truevals: List[Trueval] = []

    query = get_truevals_query(
        addresses,
        start_ts,
        end_ts,
        first,
        skip,
    )

    try:
        logger.info("Querying subgraph... %s", query)
        result = query_subgraph(
            get_subgraph_url(network),
            query,
            timeout=20.0,
        )
    except Exception as e:
        logger.info(
            "Error fetching predictTrueVals items. Exception: %s",
            e,
        )
        return []

    if "data" not in result or not result["data"]:
        return []

    data = result["data"].get("predictTrueVals", [])
    if len(data) == 0:
        return []

    for record in data:
        truevalue = record["trueValue"]
        timestamp = UnixTimeS(int(record["timestamp"]))
        ID = record["id"]
        token = record["slot"]["predictContract"]["token"]["name"]
        slot = UnixTimeS(int(record["id"].split("-")[1]))

        trueval = Trueval(
            ID=ID,
            token=token,
            timestamp=timestamp,
            truevalue=truevalue,
            slot=slot,
        )

        truevals.append(trueval)

    return truevals
