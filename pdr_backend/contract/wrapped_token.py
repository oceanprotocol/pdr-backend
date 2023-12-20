from pdr_backend.contract.token import Token
from pdr_backend.util.networkutil import tx_call_params


class WrappedToken(Token):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address)
        abi = [
            {
                "constant": False,
                "inputs": [{"type": "uint256"}],
                "name": "withdraw",
                "outputs": [],
                "payable": False,
                "stateMutability": "external",
                "type": "function",
            },
        ]
        self.contract_instance_wrapped = self.config.w3.eth.contract(
            address=self.contract_address, abi=abi
        )

    def withdraw(self, amount: int, wait_for_receipt=True):
        """
        Converts Wrapped Token to Token, amount is in wei.
        """
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance_wrapped.functions.withdraw(amount).transact(
            call_params
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
