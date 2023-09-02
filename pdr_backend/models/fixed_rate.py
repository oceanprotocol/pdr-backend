from enforce_typing import enforce_types

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class FixedRate(BaseContract):
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "FixedRateExchange")

    def get_dt_price(self, exchangeId):
        return self.contract_instance.functions.calcBaseInGivenOutDT(
            exchangeId, self.config.w3.to_wei("1", "ether"), 0
        ).call()
