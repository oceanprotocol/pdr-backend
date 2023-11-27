from abc import ABC
from enforce_typing import enforce_types

from pdr_backend.util.contract import get_contract_abi


@enforce_types
class BaseContract(ABC):
    def __init__(self, web3_pp, address: str, contract_name: str):
        super().__init__()
        from pdr_backend.ppss.web3_pp import (  # pylint: disable=import-outside-toplevel
            Web3PP,
        )

        if not isinstance(web3_pp, Web3PP):
            raise ValueError(f"web3_pp is {web3_pp.__class__}, not Web3PP")
        self.web3_pp = web3_pp
        self.config = web3_pp.web3_config  # for convenience
        self.contract_address = self.config.w3.to_checksum_address(address)
        self.contract_instance = self.config.w3.eth.contract(
            address=self.config.w3.to_checksum_address(address),
            abi=get_contract_abi(contract_name, web3_pp.address_file),
        )
