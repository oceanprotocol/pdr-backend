from pdr_backend.models.token import Token
from pdr_backend.util.web3_config import Web3Config


class WrappedToken:
    def __init__(self, config: Web3Config, address: str):
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
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=self.contract_address, abi=abi
        )

    def balanceOf(self, address: str) -> int:
        return Token(self.config, self.contract_address).balanceOf(address)

    def withdraw(self, amount: int, wait_for_receipt=True):
        """
        Converts Wrapped Token to Token, amount is in wei.
        """
        gas_price = self.config.w3.eth.gas_price

        tx = self.contract_instance.functions.withdraw(amount).transact(
            {"from": self.config.owner, "gasPrice": gas_price}
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
