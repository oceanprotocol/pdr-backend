from enforce_typing import enforce_types
from sapphirepy import wrapper

from pdr_backend.util.constants import (
    SAPPHIRE_MAINNET_CHAINID,
    SAPPHIRE_TESTNET_CHAINID,
)


@enforce_types
def is_sapphire_network(chain_id: int) -> bool:
    return chain_id in [SAPPHIRE_TESTNET_CHAINID, SAPPHIRE_MAINNET_CHAINID]


@enforce_types
def get_sapphire_postfix(network: str) -> str:
    if network == "sapphire-testnet":
        return "testnet"
    if network == "sapphire-mainnet":
        return "mainnet"

    raise ValueError(f"'{network}' is not valid name")


@enforce_types
def send_encrypted_tx(
    contract_instance,
    function_name,
    args,
    pk,
    sender,
    receiver,
    rpc_url,
    value=0,  # in wei
    gasLimit=10000000,
    gasCost=0,  # in wei
    nonce=0,
) -> tuple:
    data = contract_instance.encodeABI(fn_name=function_name, args=args)
    return wrapper.send_encrypted_sapphire_tx(
        pk,
        sender,
        receiver,
        rpc_url,
        value,
        gasLimit,
        data,
        gasCost,
        nonce,
    )


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


@enforce_types
def tx_gas_price(web3_pp) -> int:
    """Return gas price for use in call_params of transaction calls."""
    network = web3_pp.network
    if network in ["sapphire-testnet", "sapphire-mainnet"]:
        return web3_pp.web3_config.w3.eth.gas_price
        # return 100000000000
    if network in ["development", "barge-predictoor-bot", "barge-pytest"]:
        return 0
    raise ValueError(f"Unknown network {network}")


@enforce_types
def tx_call_params(web3_pp, gas=None) -> dict:
    call_params = {
        "from": web3_pp.web3_config.owner,
        "gasPrice": tx_gas_price(web3_pp),
    }
    if gas is not None:
        call_params["gas"] = gas
    return call_params


@enforce_types
def get_max_gas(web3_config) -> int:
    """Returns max block gas"""
    block = web3_config.get_block(
        web3_config.w3.eth.block_number, full_transactions=False
    )
    return int(block["gasLimit"] * 0.99)
