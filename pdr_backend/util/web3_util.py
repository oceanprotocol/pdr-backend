from enforce_typing import enforce_types
from web3 import Web3

@enforce_types
def create_wallet(rpc_url: str):
    """
    @description
        Create a new wallet with a private key using the Web3.HTTPProvider(rpc_url)
        and print the private_key and the public_key
    """
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    new_account = w3.eth.account.create()
    print(f"Private Key: {new_account._private_key.hex()}")
    print(f"Public Key: {new_account.address}")