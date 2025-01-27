import logging
from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.time_types import UnixTimeS

logger = logging.getLogger("subgraph")


def get_consume_so_far(
    feed_contracts,
    week_start_timestamp: UnixTimeS,
    consumer_address,
    subgraph_url,
):
    chunk_size = 1000  # max for subgraph = 1000
    offset = 0
    consume_so_far = float(0)
    while True:  # pylint: disable=too-many-nested-blocks
        query = """
        {
            predictContracts(skip:%s, first:%s){
                id
                token{
                    orders(where: {createdTimestamp_gt:%s, consumer_in:["%s"]}){
        		        createdTimestamp
                        consumer {
                            id
                        }
                        lastPriceValue
                    }
                }
            }
        }
        """ % (
            offset,
            chunk_size,
            week_start_timestamp,
            consumer_address.lower(),
        )
        offset += chunk_size
        try:
            result = query_subgraph(subgraph_url, query)
            new_orders = result["data"]["predictContracts"]
            if new_orders == []:
                break
            for order in new_orders:
                if order["id"] in feed_contracts:
                    if len(order["token"]["orders"]) > 0:
                        for buy in order["token"]["orders"]:
                            consume_so_far = consume_so_far + float(
                                buy["lastPriceValue"]
                            )
        except Exception as e:
            logger.warning(e)
            return consume_so_far
    return consume_so_far
