import sys
from os import getenv
from typing import List
from enforce_typing import enforce_types

from eth_account import Account
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.mathutil import to_wei, from_wei


@enforce_types
def create_accounts(n_accounts: int):
    """
    @description
        Create new accounts using the web3 provider and print the private_key and the public_key
    """
    # loop through n_wallets
    for i in range(n_accounts):
        # pylint: disable=no-value-for-parameter
        new_account = Account.create()
        print(f"\nWallet #{i}")
        print(f"Private Key: {new_account._private_key.hex()}")
        print(f"Public Key: {new_account.address}")


@enforce_types
def view_accounts(addresses: List[str], web3_pp: Web3PP):
    """
    @description
        View account balances for multiple addresses
    """
    # get assets
    native_token = NativeToken(web3_pp)
    OCEAN_addr = get_address(web3_pp, "Ocean")
    OCEAN_token = Token(web3_pp, OCEAN_addr)

    # loop through all addresses and print balances
    for address in addresses:
        native_token_balance = native_token.balanceOf(address)
        OCEAN_balance = OCEAN_token.balanceOf(address)

        print(f"\nAccount {address}")
        print(f"Native token balance: {from_wei(native_token_balance)}")
        print(f"OCEAN balance: {from_wei(OCEAN_balance)}")


@enforce_types
def fund_accounts(
    amount: float, to_addresses: List[str], web3_pp: Web3PP, is_native_token: bool
):
    """
    @description
        Fund multiple accounts using native or OCEAN tokens.
        Sends a total of (Amount * n_accounts).
    """
    if web3_pp.network not in ["sapphire-testnet", "sapphire-mainnet"]:
        print("Unknown network")
        sys.exit(1)

    token = None
    token_name = None
    if is_native_token:
        token = NativeToken(web3_pp)
        token_name = "ROSE"
    else:
        OCEAN_addr = get_address(web3_pp, "Ocean")
        token = Token(web3_pp, OCEAN_addr)
        token_name = "OCEAN"

    private_key = getenv("PRIVATE_KEY")
    assert private_key is not None, "Need PRIVATE_KEY env var"

    account = Account.from_key(private_key)  # pylint: disable=no-value-for-parameter

    for address in to_addresses:
        print(f"Sending {token_name} token to {address} for the amount of {amount} wei")
        token.transfer(
            address,
            to_wei(amount),
            account.address,
            True,
        )
