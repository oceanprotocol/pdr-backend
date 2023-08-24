
class FixedRate:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("FixedRateExchange"),
        )
        self.config = config

    def get_dt_price(self, exchangeId):
        return self.contract_instance.functions.calcBaseInGivenOutDT(
            exchangeId, self.config.w3.to_wei("1", "ether"), 0
        ).call()
