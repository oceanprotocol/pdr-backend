
class Token:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC20Template3"),
        )
        self.config = config

    def allowance(self, account, spender):
        return self.contract_instance.functions.allowance(account, spender).call()

    def balanceOf(self, account):
        return self.contract_instance.functions.balanceOf(account).call()

    def transfer(self, to: str, amount: int, sender, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.transfer(to, int(amount)).transact(
            {"from": sender, "gasPrice": gasPrice}
        )
        if wait_for_receipt:
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def approve(self, spender, amount, wait_for_receipt=True):
        gasPrice = self.config.w3.eth.gas_price
        # print(f"Approving {amount} for {spender} on contract {self.contract_address}")
        try:
            tx = self.contract_instance.functions.approve(spender, amount).transact(
                {"from": self.config.owner, "gasPrice": gasPrice}
            )
            if not wait_for_receipt:
                return tx
            return self.config.w3.eth.wait_for_transaction_receipt(tx)
        except:
            return None

