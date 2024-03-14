from enforce_typing import enforce_types
from web3.types import TxParams, Wei as Web3Wei

from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.util.currency_types import Wei


@enforce_types
class Token(BaseContract):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "ERC20Template3")

    def allowance(self, account, spender) -> Wei:
        return Wei(self.contract_instance.functions.allowance(account, spender).call())

    def balanceOf(self, account) -> Wei:
        return Wei(self.contract_instance.functions.balanceOf(account).call())

    def transfer(self, to: str, amount: Wei, sender, wait_for_receipt=True):
        call_params = self.web3_pp.tx_call_params()
        tx = self.contract_instance.functions.transfer(
            to, int(amount.amt_wei)
        ).transact(call_params)

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def approve(self, spender, amount: Wei, wait_for_receipt=True):
        call_params = self.web3_pp.tx_call_params()
        # print(f"Approving {amount} for {spender} on contract {self.contract_address}")
        tx = self.contract_instance.functions.approve(spender, amount.amt_wei).transact(
            call_params
        )

        if not wait_for_receipt:
            return tx

        return self.config.w3.eth.wait_for_transaction_receipt(tx)


class NativeToken:
    @enforce_types
    def __init__(self, web3_pp):
        self.web3_pp = web3_pp

    @property
    def w3(self):
        return self.web3_pp.web3_config.w3

    @property
    def name(self):
        return "ROSE"

    @enforce_types
    def balanceOf(self, account) -> Wei:
        return Wei(self.w3.eth.get_balance(account))

    @enforce_types
    def transfer(self, to: str, amount: Wei, sender, wait_for_receipt=True):
        gas_price = self.web3_pp.tx_gas_price()
        call_params: TxParams = {
            "from": sender,
            "gas": 25000,
            "value": Web3Wei(int(amount.amt_wei)),
            "gasPrice": gas_price,
            "to": to,
        }
        tx = self.w3.eth.send_transaction(transaction=call_params)

        if not wait_for_receipt:
            return tx
        return self.w3.eth.wait_for_transaction_receipt(tx)
