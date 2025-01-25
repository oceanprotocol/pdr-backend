import logging
import sys
from typing import Dict, Tuple

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.currency_types import Eth

logger = logging.getLogger("topup")


@enforce_types
def topup_main(ppss: PPSS):
    # if there is not enough balance, exit 1 so we know that script failed
    failed = False

    web3_pp = ppss.web3_pp
    topup_ss = ppss.topup_ss
    owner = web3_pp.web3_config.owner

    OCEAN = web3_pp.OCEAN_Token
    ROSE = web3_pp.NativeToken

    owner_OCEAN_bal = OCEAN.balanceOf(owner).to_eth()
    owner_ROSE_bal = ROSE.balanceOf(owner).to_eth()
    logger.info(
        "Topup address %s has %.2f OCEAN and %.2f ROSE",
        owner,
        owner_OCEAN_bal,
        owner_ROSE_bal,
    )

    addresses: Dict[str, str] = ppss.topup_ss.all_topup_addresses(web3_pp.network)

    for addr_label, address in addresses.items():
        OCEAN_bal = OCEAN.balanceOf(address).to_eth()
        ROSE_bal = ROSE.balanceOf(address).to_eth()

        logger.info("%s: %.2f OCEAN, %.2f ROSE", addr_label, OCEAN_bal, ROSE_bal)

        min_bal = topup_ss.get_min_bal(OCEAN, addr_label)
        topup_bal = topup_ss.get_topup_bal(OCEAN, addr_label)

        OCEAN_transferred, failed_OCEAN = do_transfer(
            OCEAN, address, owner, owner_OCEAN_bal, min_bal, topup_bal
        )

        owner_OCEAN_bal = owner_OCEAN_bal - OCEAN_transferred

        min_bal = topup_ss.get_min_bal(ROSE, addr_label)
        topup_bal = topup_ss.get_topup_bal(ROSE, addr_label)

        ROSE_transferred, failed_ROSE = do_transfer(
            ROSE, address, owner, owner_ROSE_bal, min_bal, topup_bal
        )

        owner_ROSE_bal = owner_ROSE_bal - ROSE_transferred

        if failed_ROSE or failed_OCEAN:
            failed = True

    if failed:
        sys.exit(1)

    sys.exit(0)


def do_transfer(
    token, address, owner, owner_bal, min_bal: Eth, topup_bal: Eth
) -> Tuple[Eth, bool]:
    bal = token.balanceOf(address).to_eth()

    symbol = "ROSE" if token.name == "ROSE" else "OCEAN"

    failed = False
    transfered_amount = Eth(0)

    if min_bal > Eth(0) and bal < min_bal:
        logger.info("Transferring %s %s to %s...", topup_bal.amt_eth, symbol, address)
        if owner_bal > topup_bal:
            token.transfer(
                address,
                topup_bal.to_wei(),
                owner,
                True,
            )
            transfered_amount = topup_bal
        else:
            failed = True
            logger.error("Not enough %s :(", symbol)

    return transfered_amount, failed
