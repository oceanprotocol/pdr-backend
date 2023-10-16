from enforce_typing import enforce_types
from web3.types import TxParams, Wei

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class Token(BaseContract):
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "ERC20Template3")

    def allowance(self, account, spender):
        return self.contract_instance.functions.allowance(account, spender).call()

    def balanceOf(self, account):
        return self.contract_instance.functions.balanceOf(account).call()

    def transfer(self, to: str, amount: int, sender, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.transfer(to, int(amount)).transact(
            {"from": sender, "gasPrice": gasPrice}
        )

        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def approve(self, spender, amount, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        # print(f"Approving {amount} for {spender} on contract {self.contract_address}")
        tx = self.contract_instance.functions.approve(spender, amount).transact(
            {"from": self.config.owner, "gasPrice": gasPrice}
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)


class NativeToken:
    def __init__(self, config: Web3Config):
        self.config = config

    def balanceOf(self, account):
        return self.config.w3.eth.get_balance(account)

    def transfer(self, to: str, amount: int, sender, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        params: TxParams = {
            "from": sender,
            "gas": 25000,
            "value": Wei(amount),
            "gasPrice": Wei(gasPrice),
            "to": to,
        }
        tx = self.config.w3.eth.send_transaction(transaction=params)

        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
