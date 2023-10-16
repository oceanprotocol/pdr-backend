import math
import sys
import time
from pdr_backend.models.base_config import BaseConfig
from pdr_backend.models.token import Token, NativeToken
from pdr_backend.util.contract import get_address
from addresses import get_opf_addresses


if __name__ == "__main__":
    config = BaseConfig()

    addresses = get_opf_addresses(config.web3_config.w3.eth.chain_id)
    ocean_address = get_address(config.web3_config.w3.eth.chain_id, "Ocean")
    ocean_token = Token(config.web3_config, ocean_address)
    rose = NativeToken(config.web3_config)
    for name, value in addresses.items():
        ocean_bal_wei = ocean_token.balanceOf(value)
        rose_bal_wei = rose.balanceOf(value)

        ocean_bal = ocean_bal_wei / 1e18
        rose_bal = rose_bal_wei / 1e18

        minimum_ocean_bal = 10
        minimum_rose_bal = 10
        topup_ocean_bal = 10
        topup_rose_bal = 20

        if name == "trueval":
            minimum_ocean_bal = 0
            topup_ocean_bal = 0

        if name == "dfbuyer" and config.web3_config.w3.eth.chain_id == 23294:
            minimum_ocean_bal = 0
            topup_ocean_bal = 0

        # pylint: disable=line-too-long
        print(f"{name}: OCEAN: {ocean_bal:.2f}, Native: {rose_bal:.2f}")
        # check if we need to transfer
        if minimum_ocean_bal > 0 and ocean_bal < minimum_ocean_bal:
            print(f"\t Transfering {topup_ocean_bal} OCEAN to {value}...")
            ocean_token.transfer(
                value,
                config.web3_config.w3.to_wei(topup_ocean_bal, "ether"),
                config.web3_config.owner,
                False,
            )
            time.sleep(20)
        if minimum_rose_bal > 0 and rose_bal < minimum_rose_bal:
            print(f"\t Transfering {topup_rose_bal} ROSE to {value}...")
            rose.transfer(
                value,
                config.web3_config.w3.to_wei(topup_rose_bal, "ether"),
                config.web3_config.owner,
                False,
            )
            time.sleep(20)
