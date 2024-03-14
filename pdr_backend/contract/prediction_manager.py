from enforce_typing import enforce_types
from pdr_backend.contract.base_contract import BaseContract


@enforce_types
class PredictionManager(BaseContract):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "PredictionManager")
