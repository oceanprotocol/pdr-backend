import time

from enforce_typing import enforce_types

from pdr_backend.subgraph.core_subgraph import query_subgraph
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def block_number_is_synced(subgraph_url: str, block_number: int) -> bool:
    query = """
        {
            predictContracts(block:{number:%s}){
                id
            }
        }
    """ % (
        block_number
    )
    try:
        result = query_subgraph(subgraph_url, query)
    except Exception:
        return False

    return "errors" not in result


@enforce_types
def wait_until_subgraph_syncs(web3_config: Web3Config, subgraph_url: str):
    block_number = web3_config.w3.eth.block_number
    while block_number_is_synced(subgraph_url, block_number) is not True:
        print("Subgraph is out of sync, trying again in 5 seconds")
        time.sleep(5)
