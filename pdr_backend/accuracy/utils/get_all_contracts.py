from typing import List
from pdr_backend.util.subgraph import query_subgraph
from pdr_backend.accuracy.utils.get_subgraph_url import get_subgraph_url

def get_all_contracts(owner_address: str, network: str) -> List[str]:
    if network != "mainnet" and network != "testnet":
        raise Exception("Invalid network, pick mainnet or testnet")

    # Define the GraphQL query
    query = """
    {
        tokens(where: {
            nft_: {
                owner: "%s"
            }
        }) {
            id
        }
    }
    """ % owner_address

    # Define the subgraph endpoint
    result = query_subgraph(get_subgraph_url(network), query, timeout=20.0)

    if not "data" in result:
        raise Exception("Error fetching contracts: No data returned")

    # Parse the results and construct Contract objects
    contract_data = result["data"]["tokens"]
    contracts = [contract["id"] for contract in contract_data]

    return contracts
