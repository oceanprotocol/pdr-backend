import logging
from typing import List
from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.subgraph.payout import Payout
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


@enforce_types
def get_payout_query(
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
        prediction_ids: A list of prediction identifiers to include in the query.
        first: The number of records to fetch per query (pagination limit).
        skip: The number of records to skip (pagination offset).

    Returns:
        A string representing the GraphQL query.
    """

    # asset_ids_str = str(asset_ids).replace("[", "[").replace("]", "]").replace("'", '"')
    where_query_arr = []

    for asset_id in asset_ids:
        where_query_arr.append(
            """
                {
                    timestamp_gte: %s,
                    timestamp_lte: %s,
                    prediction_contains: "%s"
                }
            """
            % (start_ts, end_ts, asset_id)
        )

    return """
        query {
            predictPayouts (
            first: %s
            skip: %s
            where: {
                or: [%s]
            }
        ) {
                id
                timestamp
                payout
                predictedValue
                prediction {
                    stake
                    user {
                        id
                    }
                    slot {
                        id
                        predictContract{
                            id
                            token{
                                name
                            }
                        }
                        revenue
                        roundSumStakesUp
                        roundSumStakes
                    }
                }
            }
        }
    """ % (
        first,
        skip,
        ", ".join(where_query_arr),
    )


@enforce_types
def filter_by_addresses(result, addresses):
    """
    Filter the result["data"]["predictPayouts"] by a list of addresses.

    Parameters:
    result (dict): The result dictionary.
    addresses (list): The list of addresses to filter by.

    Returns:
    list: The filtered list of payouts.
    """
    payouts = result["data"]["predictPayouts"]
    filtered_payouts = [
        payout
        for payout in payouts
        if payout["prediction"]["slot"]["predictContract"]["id"] in addresses
    ]

    return filtered_payouts


@enforce_types
def fetch_payouts(
    start_ts: UnixTimeS,
    end_ts: UnixTimeS,
    addresses: List[str],
    first: int,
    skip: int,
    network: str = "mainnet",
) -> List[Payout]:

    payouts: List[Payout] = []

    query = get_payout_query(
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
        logger.warning(
            "Error fetching predictPayouts, got #%d items. Exception: %s",
            len(payouts),
            e,
        )

    data = result["data"].get("predictPayouts", [])
    if len(data) == 0:
        return payouts

    new_payouts = [
        Payout(
            **{
                "payout": float(payout["payout"]),
                "user": payout["prediction"]["user"]["id"],
                "timestamp": UnixTimeS(int(payout["timestamp"])),
                "ID": payout["id"],
                "token": payout["prediction"]["slot"]["predictContract"]["token"][
                    "name"
                ],
                "slot": UnixTimeS(int(payout["id"].split("-")[1])),
                "predictedValue": bool(payout["predictedValue"]),
                "revenue": float(payout["prediction"]["slot"]["revenue"]),
                "roundSumStakesUp": float(
                    payout["prediction"]["slot"]["roundSumStakesUp"]
                ),
                "roundSumStakes": float(payout["prediction"]["slot"]["roundSumStakes"]),
                "stake": float(payout["prediction"]["stake"]),
            }
        )
        for payout in data
    ]

    payouts.extend(new_payouts)

    return payouts
