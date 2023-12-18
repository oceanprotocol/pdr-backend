import os
from typing import List

from enforce_typing import enforce_types
from eth_account import Account

from pdr_backend.models.token import Token
from pdr_backend.ppss.web3_pp import Web3PP
from pdr_backend.util.contract import get_address


@enforce_types
def fund_accounts_with_OCEAN(web3_pp: Web3PP):
    """
    Fund accounts, with opinions: use OCEAN, and choices of amounts.
    Meant to be used from CLI.
    """
    print(f"Fund accounts with OCEAN, network = {web3_pp.network}")
    accounts_to_fund = [
        #    account_key_env,   OCEAN_to_send
        ("PREDICTOOR_PRIVATE_KEY", 2000.0),
        ("PREDICTOOR2_PRIVATE_KEY", 2000.0),
        ("PREDICTOOR3_PRIVATE_KEY", 2000.0),
        ("TRADER_PRIVATE_KEY", 2000.0),
        ("DFBUYER_PRIVATE_KEY", 10000.0),
        ("PDR_WEBSOCKET_KEY", 10000.0),
        ("PDR_MM_USER", 10000.0),
    ]

    OCEAN_addr = get_address(web3_pp, "Ocean")
    OCEAN = Token(web3_pp, OCEAN_addr)
    fund_accounts(accounts_to_fund, web3_pp.web3_config.owner, OCEAN)
    print("Done funding.")


@enforce_types
def fund_accounts(accounts_to_fund: List[tuple], owner: str, token: Token):
    """Worker function to actually fund accounts"""
    for private_key_name, amount in accounts_to_fund:
        if private_key_name in os.environ:
            private_key = os.getenv(private_key_name)
            account = Account.from_key(  # pylint: disable=no-value-for-parameter
                private_key
            )
            print(
                f"Sending OCEAN to account defined by envvar {private_key_name}"
                f", with address {account.address}"
            )
            token.transfer(account.address, amount * 1e18, owner)
