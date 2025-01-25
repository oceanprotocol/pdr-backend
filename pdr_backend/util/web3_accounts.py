import logging
import sys
from os import getenv
from typing import List
from enforce_typing import enforce_types

from eth_account import Account
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.currency_types import Eth

logger = logging.getLogger("web3_accounts")


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
        logger.info("Wallet #%s", i)
        logger.info("Private Key: %s", new_account._private_key.hex())
        logger.info("Public Key: %s", new_account.address)


@enforce_types
def print_balances(addr: str, web3_pp: Web3PP):
    """
    @description
      Print account balances for the given address

    @notes
      Does *not* use logger.info on purpose. We want output to be compact.
    """
    ROSE, OCEAN = web3_pp.NativeToken, web3_pp.OCEAN_Token
    ROSE_bal: float = ROSE.balanceOf(addr).to_eth().amount
    OCEAN_bal: float = OCEAN.balanceOf(addr).to_eth().amount
    print(f"{ROSE_bal} ROSE, {OCEAN_bal} OCEAN")


@enforce_types
def fund_accounts(
    amount: Eth, to_addresses: List[str], web3_pp: Web3PP, is_native_token: bool
):
    """
    @description
        Fund multiple accounts using native or OCEAN tokens.
        Sends a total of (Amount * n_accounts).
    """
    private_key = getenv("PRIVATE_KEY")
    assert private_key is not None, "Need PRIVATE_KEY env var"

    if web3_pp.network not in ["sapphire-testnet", "sapphire-mainnet"]:
        logger.error("Unknown network %s", web3_pp.network)
        sys.exit(1)

    token = web3_pp.NativeToken if is_native_token else web3_pp.OCEAN_Token

    assert hasattr(token, "name")
    assert hasattr(token, "transfer")

    account = Account.from_key(private_key)  # pylint: disable=no-value-for-parameter

    for address in to_addresses:
        logger.info(
            "Sending %s to %s for the amount of %s", token.name, address, amount
        )
        token.transfer(
            address,
            amount.to_wei(),
            account.address,
            True,
        )
