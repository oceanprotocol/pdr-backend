import sys
from addresses import get_opf_addresses
from pdr_backend.models.base_config import BaseConfig
from pdr_backend.models.token import Token, NativeToken


if __name__ == "__main__":
    config = BaseConfig()
    failed = (
        False  # if there is not enough balance, exit 1 so we know that script failed
    )
    addresses = get_opf_addresses(config.web3_config.w3.eth.chain_id)
    ocean_address = None
    if config.web3_config.w3.eth.chain_id == 23294:  # mainnet
        ocean_address = "0x39d22B78A7651A76Ffbde2aaAB5FD92666Aca520"
    if config.web3_config.w3.eth.chain_id == 23295:  # testnet
        ocean_address = "0x973e69303259B0c2543a38665122b773D28405fB"
    if ocean_address is None:
        print("Unknown network")
        sys.exit(1)

    ocean_token = Token(config.web3_config, ocean_address)
    rose = NativeToken(config.web3_config)

    owner_ocean_balance = int(ocean_token.balanceOf(config.web3_config.owner)) / 1e18
    owner_rose_balance = int(rose.balanceOf(config.web3_config.owner)) / 1e18
    print(
        f"Topup address ({config.web3_config.owner}) has "
        + f"{owner_ocean_balance:.2f} OCEAN and {owner_rose_balance:.2f} ROSE\n\n"
    )
    total_ocean = 0
    total_rose = 0
    for name, value in addresses.items():
        ocean_bal_wei = ocean_token.balanceOf(value)
        rose_bal_wei = rose.balanceOf(value)

        ocean_bal = ocean_bal_wei / 1e18
        rose_bal = rose_bal_wei / 1e18

        minimum_ocean_bal = 20
        minimum_rose_bal = 10
        topup_ocean_bal = 20
        topup_rose_bal = 30

        if name == "trueval":
            minimum_ocean_bal = 0
            topup_ocean_bal = 0

        if name == "dfbuyer":
            minimum_ocean_bal = 0
            topup_ocean_bal = 0
            minimum_rose_bal = 50
            topup_rose_bal = 50

        # pylint: disable=line-too-long
        print(f"{name}: {ocean_bal:.2f} OCEAN, {rose_bal:.2f} ROSE")
        # check if we need to transfer
        if minimum_ocean_bal > 0 and ocean_bal < minimum_ocean_bal:
            print(f"\t Transfering {topup_ocean_bal} OCEAN to {value}...")
            if owner_ocean_balance > topup_ocean_bal:
                ocean_token.transfer(
                    value,
                    config.web3_config.w3.to_wei(topup_ocean_bal, "ether"),
                    config.web3_config.owner,
                    True,
                )
                owner_ocean_balance = owner_ocean_balance - topup_ocean_bal
            else:
                failed = True
                print("Not enough OCEAN :(")
        if minimum_rose_bal > 0 and rose_bal < minimum_rose_bal:
            print(f"\t Transfering {topup_rose_bal} ROSE to {value}...")
            if owner_rose_balance > topup_rose_bal:
                rose.transfer(
                    value,
                    config.web3_config.w3.to_wei(topup_rose_bal, "ether"),
                    config.web3_config.owner,
                    True,
                )
                owner_rose_balance = owner_rose_balance - topup_rose_bal
            else:
                failed = True
                print("Not enough ROSE :(")
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)
