from enforce_typing import enforce_types

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class DFRewards(BaseContract):
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "DFRewards")

    def claim_rewards(self, user_addr: str, token_addr: str, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.claimFor(user_addr, token_addr).transact(
            {"from": self.config.owner, "gasPrice": gasPrice}
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def get_claimable_rewards(self, user_addr: str, token_addr: str) -> float:
        claimable_wei = self.contract_instance.functions.claimable(
            user_addr, token_addr
        ).call()
        claimable_rewards = self.config.w3.from_wei(claimable_wei, "ether")
        return float(claimable_rewards)
