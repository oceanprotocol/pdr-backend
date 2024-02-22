import json
import logging
from typing import List

from enforce_typing import enforce_types

from pdr_backend.subgraph.subscription import Subscription
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.info725 import info725_to_info
from pdr_backend.util.networkutil import get_subgraph_url
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


@enforce_types
def fetch_filtered_subscriptions(
    start_ts: UnixTimeS,
    end_ts: UnixTimeS,
    contracts: List[str],
    first: int,
    skip: int,
    network: str,
) -> List[Subscription]:
    """
    Fetches subscriptions from predictoor subgraph within a specified time range
    and according to given contracts.

    This function supports querying subscriptions based on contract
    addresses. It iteratively queries the subgraph in chunks to retrieve all relevant
    subscriptions and returns a dataframe as a result.

    Args:
        start_ts: The starting Unix timestamp for the query range.
        end_ts: The ending Unix timestamp for the query range.
        contracts: A list of strings representing the filter
            values (contract addresses).
        network: A string indicating the blockchain network to query ('mainnet' or 'testnet').

    Returns:
        A dataframe of predictSubscriptions objects that match the filter criteria

    Raises:
        Exception: If the specified network is neither 'mainnet' nor 'testnet'.
    """

    if network not in ["mainnet", "testnet"]:
        raise Exception("Invalid network, pick mainnet or testnet")

    subscriptions: List[Subscription] = []

    # Convert contracts to lowercase
    contracts = [f.lower() for f in contracts]

    # pylint: disable=line-too-long
    if len(contracts) > 0:
        where_clause = f", where: {{predictContract_: {{id_in: {json.dumps(contracts)}}}, timestamp_gt: {start_ts}, timestamp_lt: {end_ts}}}"
    else:
        where_clause = f", where: {{timestamp_gt: {start_ts}, timestamp_lt: {end_ts}}}"

    # pylint: disable=line-too-long
    query = f"""
        {{
            predictSubscriptions(skip: {skip}, first: {first} {where_clause}) {{
                id
                txId
                timestamp
                user {{
                    id
                }}
                predictContract {{
                    id
                    token {{
                        id
                        name
                        lastPriceValue
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

    logger.info("Querying subgraph... %s", query)
    result = query_subgraph(
        get_subgraph_url(network),
        query,
        timeout=20.0,
    )

    if "data" not in result or not result["data"]:
        return []

    data = result["data"].get("predictSubscriptions", [])
    if len(data) == 0:
        return []

    for subscription_sg_dict in data:
        info725 = subscription_sg_dict["predictContract"]["token"]["nft"]["nftData"]
        info = info725_to_info(info725)
        pair = info["pair"]
        timeframe = info["timeframe"]
        source = info["source"]
        timestamp = UnixTimeS(int(subscription_sg_dict["timestamp"]))
        tx_id = subscription_sg_dict["txId"]
        last_price_value = (
            float(subscription_sg_dict["predictContract"]["token"]["lastPriceValue"])
            * 1.201
        )

        user = subscription_sg_dict["user"]["id"]

        subscription = Subscription(
            ID=subscription_sg_dict["id"],
            pair=pair,
            timeframe=timeframe,
            source=source,
            timestamp=timestamp,
            tx_id=tx_id,
            last_price_value=last_price_value,
            user=user,
        )
        subscriptions.append(subscription)

    return subscriptions
