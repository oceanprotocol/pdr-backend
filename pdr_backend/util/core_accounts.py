import logging
import os
from typing import List

from enforce_typing import enforce_types
from eth_account import Account

from pdr_backend.contract.token import Token
from pdr_backend.ppss.web3_pp import Web3PP

logger = logging.getLogger(__name__)


@enforce_types
def fund_accounts_with_OCEAN(web3_pp: Web3PP):
    """
    Fund accounts, with opinions: use OCEAN, and choices of amounts.
    Meant to be used from CLI.
    """
    logger.info("Fund accounts with OCEAN, network = %s", web3_pp.network)
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

    OCEAN = web3_pp.OCEAN_Token
    _fund_accounts(accounts_to_fund, web3_pp.web3_config.owner, OCEAN)
    logger.info("Done funding.")


@enforce_types
def _fund_accounts(accounts_to_fund: List[tuple], owner: str, token: Token):
    """Worker function to actually fund accounts"""
    for private_key_name, amount in accounts_to_fund:
        if private_key_name in os.environ:
            private_key = os.getenv(private_key_name)
            account = Account.from_key(  # pylint: disable=no-value-for-parameter
                private_key
            )
            logger.info(
                "Sending OCEAN to account defined by envvar %s, with address %s",
                private_key_name,
                account.address,
            )
            token.transfer(account.address, amount * 1e18, owner)
