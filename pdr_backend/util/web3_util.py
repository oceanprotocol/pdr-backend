import sys
from typing import List
from enforce_typing import enforce_types

from os import getenv

from web3 import Web3
from eth_account import Account
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.mathutil import to_wei


@enforce_types
def create_wallets(n_wallets: int, rpc_url: str):
    """
    @description
        Create a new wallet with a private key using the Web3.HTTPProvider(rpc_url)
        and print the private_key and the public_key
    """
    # loop through n_wallets
    for i in range(n_wallets):
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        new_account = w3.eth.account.create()
        print(f"\nWallet #{i}")
        print(f"Private Key: {new_account._private_key.hex()}")
        print(f"Public Key: {new_account.address}")


@enforce_types
def fund_wallets_with_amount(amount: float, to_addressess: List[str], web3_pp: Web3PP, is_native_token: bool):
    """
    @description
        Fund the wllets using with native token or OCEAN
    """
    if web3_pp.network not in ["sapphire-testnet", "sapphire-mainnet"]:
        print("Unknown network")
        sys.exit(1)
    
    token = None
    token_name = None
    if is_native_token:
        token = NativeToken(web3_pp)
        token_name = "ROSE"
    else :
        OCEAN_addr = get_address(web3_pp, "Ocean")
        token = Token(web3_pp, OCEAN_addr)
        token_name = "OCEAN"

    private_key = getenv("PRIVATE_KEY")
    assert private_key is not None, "Need PRIVATE_KEY env var"
    
    account = Account.from_key(  # pylint: disable=no-value-for-parameter
        private_key
    )

    for address in to_addressess:
        print(f"Sending {token_name} token to {address} for the amount of {amount} wei")
        token.transfer(
            address,
            to_wei(amount),
            account.address,
            True,
        )