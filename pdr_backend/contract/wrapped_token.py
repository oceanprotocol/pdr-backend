#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from pdr_backend.contract.token import Token
from pdr_backend.util.currency_types import Wei


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

    def withdraw(self, amount: Wei, wait_for_receipt=True):
        """
        Converts Wrapped Token to Token, amount is in wei.
        """
        call_params = self.web3_pp.tx_call_params()
        unsigned = self.contract_instance_wrapped.functions.withdraw(
            amount.amt_wei
        ).build_transaction(call_params)
        tx = self._sign_and_send_transaction(unsigned, call_params)

        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
