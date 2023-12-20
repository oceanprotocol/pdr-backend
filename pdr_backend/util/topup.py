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
    if web3_pp.network not in ["sapphire-testnet", "sapphire-mainnet"]:
        print("Unknown network")
        sys.exit(1)

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

        min_OCEAN_bal, topup_OCEAN_bal = 20, 20
        min_ROSE_bal, topup_ROSE_bal = 30, 30

        if addr_label == "trueval":
            min_OCEAN_bal, topup_OCEAN_bal = 0, 0
        elif addr_label == "dfbuyer":
            min_OCEAN_bal, topup_OCEAN_bal = 0, 0
            min_ROSE_bal, topup_ROSE_bal = 250, 250

        print(f"{addr_label}: {OCEAN_bal:.2f} OCEAN, {ROSE_bal:.2f} ROSE")

        # check if we need to transfer
        if min_OCEAN_bal > 0 and OCEAN_bal < min_OCEAN_bal:
            print(f"\t Transferring {topup_OCEAN_bal} OCEAN to {address}...")
            if owner_OCEAN_bal > topup_OCEAN_bal:
                OCEAN.transfer(
                    address,
                    to_wei(topup_OCEAN_bal),
                    owner,
                    True,
                )
                owner_OCEAN_bal = owner_OCEAN_bal - topup_OCEAN_bal
            else:
                failed = True
                print("Not enough OCEAN :(")

        if min_ROSE_bal > 0 and ROSE_bal < min_ROSE_bal:
            print(f"\t Transferring {topup_ROSE_bal} ROSE to {address}...")
            if owner_ROSE_bal > topup_ROSE_bal:
                ROSE.transfer(
                    address,
                    to_wei(topup_ROSE_bal),
                    owner,
                    True,
                )
                owner_ROSE_bal = owner_ROSE_bal - topup_ROSE_bal
            else:
                failed = True
                print("Not enough ROSE :(")

    if failed:
        sys.exit(1)
    sys.exit(0)
