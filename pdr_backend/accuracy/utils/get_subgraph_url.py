def get_subgraph_url(network: str) -> str:
    """
    Returns the subgraph URL for the given network.

    Args:
        network (str): The network name ("mainnet" or "testnet").

    Returns:
        str: The subgraph URL for the specified network.
    """
    if network not in ["mainnet", "testnet"]:
        raise ValueError("Invalid network. Acceptable values are 'mainnet' or 'testnet'.")

    return f"https://v4.subgraph.sapphire-{network}.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
