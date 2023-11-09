from enforce_typing import enforce_types

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class DFRewards(BaseContract):
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "DFRewards")

    def claim_rewards(self, address: str):
        pass
    
    def get_available_rewards(self, address:str) -> float:
        pass