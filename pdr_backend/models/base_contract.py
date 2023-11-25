from abc import ABC
from enforce_typing import enforce_types

from pdr_backend.util.contract import get_contract_abi
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class BaseContract(ABC):
    def __init__(self, config: Web3Config, address: str, name: str):
        super().__init__()
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi(name),
        )
