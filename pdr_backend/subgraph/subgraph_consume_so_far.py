#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from collections import defaultdict
import logging
from typing import Dict, List

from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


@enforce_types
def get_consume_so_far_per_contract(
    subgraph_url: str,
    user_address: str,
    since_timestamp: UnixTimeS,
    contract_addresses: List[str],
) -> Dict[str, float]:
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    consume_so_far: Dict[str, float] = defaultdict(float)
    print("Getting consume so far...")
    while True:
        query = """
        {
            predictSubscriptions(where: {timestamp_gt:%s, user_:{id: "%s"}}, first: %s, skip: %s){
                id
                timestamp
                user {
                id
                }
                predictContract {
                id
                }
            }
        }
        """ % (
            since_timestamp,
            user_address.lower(),
            chunk_size,
            offset,
        )
        offset += chunk_size
        result = query_subgraph(subgraph_url, query, 3, 30.0)
        if "data" not in result or "predictSubscriptions" not in result["data"]:
            raise Exception("Error getting subscription data")
        subscriptions = result["data"]["predictSubscriptions"]
        if subscriptions == []:
            break
        for sub in subscriptions:
            contract_address = sub["predictContract"]["id"]
            if contract_address not in contract_addresses:
                continue
            consume_so_far[contract_address] += 3.0
    return consume_so_far
