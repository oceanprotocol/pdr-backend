import json
from enum import Enum
from typing import List, TypedDict

from enforce_typing import enforce_types

from pdr_backend.contract.subscription import Subscription
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.info725 import info725_to_info
from pdr_backend.util.networkutil import get_subgraph_url


@enforce_types
def fetch_filtered_subscriptions(
    start_ts: int,
    end_ts: int,
    filters: List[str],
    network: str,
) -> List[Subscription]:
    """
    Fetches subscriptions from predictoor subgraph within a specified time range
    and according to given filters.

    This function supports querying subscriptions based on contract
    addresses. It iteratively queries the subgraph in chunks to retrieve all relevant
    subscriptions and returns a dataframe as a result.

    Args:
        start_ts: The starting Unix timestamp for the query range.
        end_ts: The ending Unix timestamp for the query range.
        filters: A list of strings representing the filter
            values (contract addresses).
        network: A string indicating the blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dataframe of predictSubscriptions objects that match the filter criteria within the given time range.

    Raises:
        Exception: If the specified network is neither 'mainnet' nor 'testnet'.
    """

    if network not in ["mainnet", "testnet"]:
        raise Exception("Invalid network, pick mainnet or testnet")

    chunk_size = 1000
    offset = 0
    subscriptions: List[Subscription] = []

    # Convert filters to lowercase
    filters = [f.lower() for f in filters]

    # pylint: disable=line-too-long
    if len(filters) > 0:
        where_clause = f", where: {{predictContract_: {{id_in: {json.dumps(filters)}, timestamp_gt: {start_ts}, timestamp_lt: {end_ts}}}}}"
    else:
        where_clause = f", where: {{timestamp_gt: {start_ts}, timestamp_lt: {end_ts}}}"

    while True:
        query = f"""
            {{
                predictSubscriptions(skip: {offset}, first: {chunk_size} {where_clause}) {{
                    id
                    txId
                    timestamp
                    eventIndex
                    user {{
                        id
                    }}
                    predictContract {{
                        id
                        token {{
                            id
                            name
                            nft{{
                                nftData {{
                                key
                                value
                                }}
                            }}
                        }}
                    }}
                }}
            }}"""

        print("Querying subgraph...", query)
        result = query_subgraph(
            get_subgraph_url(network),
            query,
            timeout=20.0,
        )

        offset += chunk_size

        if not "data" in result:
            break

        data = result["data"]["predictSubscriptions"]
        if len(data) == 0:
            break

        for subscription_sg_dict in data:
            info725 = subscription_sg_dict["predictContract"]["token"]["nft"][
                "nftData"
            ]
            info = info725_to_info(info725)
            pair = info["pair"]
            timeframe = info["timeframe"]
            source = info["source"]
            timestamp = subscription_sg_dict["timestamp"]
            tx_id = subscription_sg_dict["txId"]
            event_index = subscription_sg_dict["eventIndex"]
            user = subscription_sg_dict["user"]["id"]

            subscription = Subscription(
                ID=subscription_sg_dict["id"],
                pair=pair,
                timeframe=timeframe,
                source=source,
                timestamp=timestamp,
                tx_id=tx_id,
                event_index=event_index,
                user=user,
            )
            subscriptions.append(subscription)

    return subscriptions
