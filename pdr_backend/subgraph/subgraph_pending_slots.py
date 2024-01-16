import time
from typing import List, Optional

from pdr_backend.cli.arg_feeds import ArgFeeds
from pdr_backend.contract.slot import Slot
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.subgraph.info725 import info725_to_info
from pdr_backend.subgraph.subgraph_feed import SubgraphFeed


# don't use @enforce_types here, it causes issues
def get_pending_slots(
    subgraph_url: str,
    timestamp: int,
    owner_addresses: Optional[List[str]],
    allowed_feeds: Optional[ArgFeeds] = None,
):
    chunk_size = 1000
    offset = 0
    owners: Optional[List[str]] = owner_addresses

    slots: List[Slot] = []

    now_ts = time.time()
    # rounds older than 3 days are canceled + 10 min buffer
    three_days_ago = int(now_ts - 60 * 60 * 24 * 3 + 10 * 60)

    while True:
        query = """
        {
            predictSlots(where: {slot_gt: %s, slot_lte: %s, status: "Pending"}, skip:%s, first:%s){
                id
                slot
                status
                trueValues {
                    id
                }
                predictContract {
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
        }
        """ % (
            three_days_ago,
            timestamp,
            offset,
            chunk_size,
        )

        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            if not "data" in result:
                print("No data in result")
                break
            slot_list = result["data"]["predictSlots"]
            if slot_list == []:
                break
            for slot in slot_list:
                if slot["trueValues"] != []:
                    continue

                contract = slot["predictContract"]
                info725 = contract["token"]["nft"]["nftData"]
                info = info725_to_info(info725)

                pair = info["pair"]
                timeframe = info["timeframe"]
                source = info["source"]
                assert pair, "need a pair"
                assert timeframe, "need a timeframe"
                assert source, "need a source"

                owner_id = contract["token"]["nft"]["owner"]["id"]
                if owners and (owner_id not in owners):
                    continue

                if allowed_feeds and not allowed_feeds.contains_combination(
                    source, pair, timeframe
                ):
                    continue

                feed = SubgraphFeed(
                    name=contract["token"]["name"],
                    address=contract["id"],
                    symbol=contract["token"]["symbol"],
                    seconds_per_subscription=int(contract["secondsPerSubscription"]),
                    trueval_submit_timeout=int(contract["truevalSubmitTimeout"]),
                    owner=contract["token"]["nft"]["owner"]["id"],
                    pair=pair,
                    timeframe=timeframe,
                    source=source,
                )

                slot_number = int(slot["slot"])
                slot = Slot(slot_number, feed)
                slots.append(slot)

        except Exception as e:
            print(e)
            break

    return slots
