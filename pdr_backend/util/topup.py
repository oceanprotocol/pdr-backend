import sys
from typing import Dict

from enforce_typing import enforce_types

from pdr_backend.models.token import Token, NativeToken
from pdr_backend.ppss.ppss import PPSS
from pdr_backend.util.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
    OCEAN_TOKEN_ADDRS,
)
from pdr_backend.util.constants_opf_addrs import get_opf_addresses


@enforce_types
def topup_main(ppss: PPSS):
    # if there is not enough balance, exit 1 so we know that script failed
    failed = False

    web3_config = ppss.web3_pp.web3_config
    chain_id = web3_config.w3.eth.chain_id
    if chain_id not in [SAPPHIRE_MAINNET_CHAINID, SAPPHIRE_TESTNET_CHAINID]:
        print("Unknown network")
        sys.exit(1)

    OCEAN = Token(ppss.web3_pp, OCEAN_TOKEN_ADDRS[chain_id])
    ROSE = NativeToken(ppss.web3_pp)

    owner_OCEAN_bal = int(OCEAN.balanceOf(web3_config.owner)) / 1e18
    owner_ROSE_bal = int(ROSE.balanceOf(web3_config.owner)) / 1e18
    print(
        f"Topup address ({web3_config.owner}) has "
        + f"{owner_OCEAN_bal:.2f} OCEAN and {owner_ROSE_bal:.2f} ROSE\n\n"
    )

    addresses: Dict[str, str] = get_opf_addresses(chain_id)
    for addr_label, address in addresses.items():
        OCEAN_bal_wei = OCEAN.balanceOf(address)
        ROSE_bal_wei = ROSE.balanceOf(address)

        OCEAN_bal = OCEAN_bal_wei / 1e18
        ROSE_bal = ROSE_bal_wei / 1e18

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
                    web3_config.w3.to_wei(topup_OCEAN_bal, "ether"),
                    web3_config.owner,
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
                    web3_config.w3.to_wei(topup_ROSE_bal, "ether"),
                    web3_config.owner,
                    True,
                )
                owner_ROSE_bal = owner_ROSE_bal - topup_ROSE_bal
            else:
                failed = True
                print("Not enough ROSE :(")

    if failed:
        sys.exit(1)
    sys.exit(0)
