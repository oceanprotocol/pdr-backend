import logging
import sys
from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.mathutil import from_wei, to_wei

logger = logging.getLogger(__name__)


@enforce_types
def topup_main(ppss: PPSS):
    # if there is not enough balance, exit 1 so we know that script failed
    failed = False

    web3_pp = ppss.web3_pp
    topup_ss = ppss.topup_ss
    owner = web3_pp.web3_config.owner

    OCEAN = web3_pp.OCEAN_Token
    ROSE = web3_pp.NativeToken

    owner_OCEAN_bal = from_wei(OCEAN.balanceOf(owner))
    owner_ROSE_bal = from_wei(ROSE.balanceOf(owner))
    logger.info(
        f"Topup address ({owner}) has "
        + f"{owner_OCEAN_bal:.2f} OCEAN and {owner_ROSE_bal:.2f} ROSE\n\n"
    )

    addresses: Dict[str, str] = ppss.topup_ss.all_topup_addresses(web3_pp.network)

    for addr_label, address in addresses.items():
        OCEAN_bal = from_wei(OCEAN.balanceOf(address))
        ROSE_bal = from_wei(ROSE.balanceOf(address))

        logger.info(f"{addr_label}: {OCEAN_bal:.2f} OCEAN, {ROSE_bal:.2f} ROSE")

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


def do_transfer(token, address, owner, owner_bal, min_bal, topup_bal):
    bal = from_wei(token.balanceOf(address))

    symbol = "ROSE" if token.name == "ROSE" else "OCEAN"

    failed = False
    transfered_amount = 0

    if min_bal > 0 and bal < min_bal:
        logger.info(f"\t Transferring {topup_bal} {symbol} to {address}...")
        if owner_bal > topup_bal:
            token.transfer(
                address,
                to_wei(topup_bal),
                owner,
                True,
            )
            transfered_amount = topup_bal
        else:
            failed = True
            logger.error(f"Not enough {symbol} :(")

    return transfered_amount, failed
