from collections import defaultdict
from typing import Dict, List

from enforce_typing import enforce_types
from pdr_backend.subgraph.core_subgraph import query_subgraph


@enforce_types
def get_consume_so_far_per_contract(
    subgraph_url: str,
    user_address: str,
    since_timestamp: int,
    contract_addresses: List[str],
) -> Dict[str, float]:
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    consume_so_far: Dict[str, float] = defaultdict(float)
    print("Getting consume so far...")
    while True:  # pylint: disable=too-many-nested-blocks
        query = """
        {
            predictContracts(first:1000, where: {id_in: %s}){
                id	
                token{
                    id
                    name
                    symbol
                    nft {
                        owner {
                            id
                        }
                        nftData {
                            key
                            value
                        }
                    }
                    orders(where: {createdTimestamp_gt:%s, consumer_in:["%s"]}, first: %s, skip: %s){
        		        createdTimestamp
                        consumer {
                            id
                        }
                        lastPriceValue
                    }
                }
                secondsPerEpoch
                secondsPerSubscription
                truevalSubmitTimeout
            }
        }
        """ % (
            str(contract_addresses).replace("'", '"'),
            since_timestamp,
            user_address.lower(),
            chunk_size,
            offset,
        )
        offset += chunk_size
        result = query_subgraph(subgraph_url, query, 3, 30.0)
        if "data" not in result or "predictContracts" not in result["data"]:
            break
        contracts = result["data"]["predictContracts"]
        if contracts == []:
            break
        no_of_zeroes = 0
        for contract in contracts:
            contract_address = contract["id"]
            if contract_address not in contract_addresses:
                continue
            order_count = len(contract["token"]["orders"])
            if order_count == 0:
                no_of_zeroes += 1
            for buy in contract["token"]["orders"]:
                # 1.2 20% fee
                # 0.001 0.01% community swap fee
                consume_amt = float(buy["lastPriceValue"]) * 1.201
                consume_so_far[contract_address] += consume_amt
        if no_of_zeroes == len(contracts):
            break
    return consume_so_far
