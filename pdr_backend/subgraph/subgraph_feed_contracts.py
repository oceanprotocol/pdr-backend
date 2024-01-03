from typing import Dict, Optional

from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.info725 import info725_to_info
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed

_N_ERRORS = {}  # exception_str : num_occurrences
_N_THR = 3


@enforce_types
def query_feed_contracts(
    subgraph_url: str,
    owners_string: Optional[str] = None,
) -> Dict[str, SubgraphFeed]:
    """
    @description
      Query the chain for prediction feed contracts.

    @arguments
      subgraph_url -- e.g.
      owners -- E.g. filter to "0x123,0x124". If None or "", allow all

    @return
      feeds -- dict of [feed_addr] : SubgraphFeed
    """
    owners = None
    if owners_string:
        owners = owners_string.lower().split(",")

    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    feeds: Dict[str, SubgraphFeed] = {}

    while True:
        query = """
        {
            predictContracts(skip:%s, first:%s){
                id
                token {
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
                }
                secondsPerEpoch
                secondsPerSubscription
                truevalSubmitTimeout
            }
        }
        """ % (
            offset,
            chunk_size,
        )
        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            contract_list = result["data"]["predictContracts"]
            if not contract_list:
                break
            for contract in contract_list:
                info725 = contract["token"]["nft"]["nftData"]
                info = info725_to_info(info725)  # {"pair": "ETH/USDT", }

                pair = info["pair"]
                timeframe = info["timeframe"]
                source = info["source"]
                if None in (pair, timeframe, source):
                    continue

                # filter out unwanted
                owner_id = contract["token"]["nft"]["owner"]["id"]
                if owners and (owner_id not in owners):
                    continue

                # ok, add this one
                feed = SubgraphFeed(
                    name=contract["token"]["name"],
                    address=contract["id"],
                    symbol=contract["token"]["symbol"],
                    seconds_per_subscription=int(contract["secondsPerSubscription"]),
                    trueval_submit_timeout=int(contract["truevalSubmitTimeout"]),
                    owner=owner_id,
                    pair=pair,
                    timeframe=timeframe,
                    source=source,
                )
                feeds[feed.address] = feed

        except Exception as e:
            e_str = str(e)
            e_key = e_str
            if "Connection object" in e_str:
                i = e_str.find("Connection object") + len("Connection object")
                e_key = e_key[:i]

            if e_key not in _N_ERRORS:
                _N_ERRORS[e_key] = 0
            _N_ERRORS[e_key] += 1

            if _N_ERRORS[e_key] <= _N_THR:
                print(e_str)
            if _N_ERRORS[e_key] == _N_THR:
                print("Future errors like this will be hidden")
            return {}

    # postconditions
    for feed in feeds.values():
        assert isinstance(feed, SubgraphFeed)

    return feeds
