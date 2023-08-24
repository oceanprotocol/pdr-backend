
def is_sapphire_network(chain_id: int) -> bool:
    return chain_id in [SAPPHIRE_TESTNET_CHAINID, SAPPHIRE_MAINNET_CHAINID]


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

