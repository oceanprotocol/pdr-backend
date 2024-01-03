from enforce_typing import enforce_types

from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.util.mathutil import from_wei
from pdr_backend.util.networkutil import tx_call_params


@enforce_types
class DFRewards(BaseContract):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "DFRewards")

    def claim_rewards(self, user_addr: str, token_addr: str, wait_for_receipt=True):
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance.functions.claimFor(user_addr, token_addr).transact(
            call_params
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def get_claimable_rewards(self, user_addr: str, token_addr: str) -> float:
        """
        @return
          claimable -- # claimable rewards (in units of ETH, not wei)
        """
        claimable_wei = self.contract_instance.functions.claimable(
            user_addr, token_addr
        ).call()
        claimable = from_wei(claimable_wei)
        return claimable
