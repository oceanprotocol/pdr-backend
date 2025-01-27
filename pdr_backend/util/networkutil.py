from enforce_typing import enforce_types


@enforce_types
def get_sapphire_postfix(network: str) -> str:
    if network == "sapphire-testnet":
        return "testnet"
    if network == "sapphire-mainnet":
        return "mainnet"

    raise ValueError(f"'{network}' is not valid name")


@enforce_types
def get_subgraph_url(network: str) -> str:
    """
    Returns the subgraph URL for the given network.

    Args:
        network (str): The network name ("mainnet" or "testnet").

    Returns:
        str: The subgraph URL for the specified network.
    """
    if network not in ["mainnet", "testnet"]:
        raise ValueError(
            "Invalid network. Acceptable values are 'mainnet' or 'testnet'."
        )

    # pylint: disable=line-too-long
    return f"https://v4.subgraph.sapphire-{network}.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
