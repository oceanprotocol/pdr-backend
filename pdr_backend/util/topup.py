import sys
from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.contract.token import NativeToken, Token
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.constants_opf_addrs import get_opf_addresses
from pdr_backend.util.contract import get_address
from pdr_backend.util.mathutil import from_wei, to_wei


@enforce_types
def topup_main(ppss: PPSS):
    # if there is not enough balance, exit 1 so we know that script failed
    failed = False

    web3_pp = ppss.web3_pp
    owner = web3_pp.web3_config.owner
    OCEAN_addr = get_address(ppss.web3_pp, "Ocean")
    OCEAN = Token(ppss.web3_pp, OCEAN_addr)
    ROSE = NativeToken(ppss.web3_pp)

    owner_OCEAN_bal = from_wei(OCEAN.balanceOf(owner))
    owner_ROSE_bal = from_wei(ROSE.balanceOf(owner))
    print(
        f"Topup address ({owner}) has "
        + f"{owner_OCEAN_bal:.2f} OCEAN and {owner_ROSE_bal:.2f} ROSE\n\n"
    )

    addresses: Dict[str, str] = get_opf_addresses(web3_pp.network)

    for addr_label, address in addresses.items():
        OCEAN_bal = from_wei(OCEAN.balanceOf(address))
        ROSE_bal = from_wei(ROSE.balanceOf(address))

        print(f"{addr_label}: {OCEAN_bal:.2f} OCEAN, {ROSE_bal:.2f} ROSE")

        OCEAN_transferred, failed_OCEAN = do_transfer(
            OCEAN, address, addr_label, owner, owner_OCEAN_bal
        )

        owner_OCEAN_bal = owner_OCEAN_bal - OCEAN_transferred

        ROSE_transferred, failed_ROSE = do_transfer(
            ROSE, address, addr_label, owner, owner_ROSE_bal
        )

        owner_ROSE_bal = owner_ROSE_bal - ROSE_transferred

        if failed_ROSE or failed_OCEAN:
            failed = True

    if failed:
        sys.exit(1)

    sys.exit(0)


def do_transfer(token, address, addr_label, owner, owner_bal):
    bal = from_wei(token.balanceOf(address))

    if token.name == "ROSE":
        min_bal = 250 if addr_label == "dfbuyer" else 30
        topup_bal = 250 if addr_label == "dfbuyer" else 30
    else:
        min_bal = 0 if addr_label in ["trueval", "dfbuyer"] else 20
        topup_bal = 0 if addr_label in ["trueval", "dfbuyer"] else 20

    failed = False
    transfered_amount = 0

    if min_bal > 0 and bal < min_bal:
        print(f"\t Transferring {topup_bal} {token.name} to {address}...")
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
            print(f"Not enough {token.name} :(")

    return transfered_amount, failed
