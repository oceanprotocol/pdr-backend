from typing import List
from eth_typing import ChecksumAddress
from pdr_backend.util.contract import get_contract_abi
from pdr_backend.util.web3_config import Web3Config


# FIX ME - Add enforce_types
class PredictoorBatcher:
    def __init__(self, config: Web3Config, address: str):
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("PredictoorHelper"),
        )
        self.contract_address = config.w3.to_checksum_address(address)

    def consume_multiple(
        self,
        addresses: List[ChecksumAddress],
        times: List[int],
        token_addr: str,
        wait_for_receipt=True,
    ):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.consumeMultiple(
            addresses, times, token_addr
        ).transact({"from": self.config.owner, "gasPrice": gasPrice})
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def submit_truevals_contracts(
        self,
        contract_addrs: List[ChecksumAddress],
        epoch_starts: List[List[int]],
        trueVals: List[List[bool]],
        cancelRounds: List[List[bool]],
        wait_for_receipt=True,
    ):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.submitTruevalContracts(
            contract_addrs, epoch_starts, trueVals, cancelRounds
        ).transact({"from": self.config.owner, "gasPrice": gasPrice})
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)

    def submit_truevals(
        self,
        contract_addr: ChecksumAddress,
        epoch_starts: List[int],
        trueVals: List[bool],
        cancelRounds: List[bool],
        wait_for_receipt=True,
    ):
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.submitTruevals(
            contract_addr, epoch_starts, trueVals, cancelRounds
        ).transact({"from": self.config.owner, "gasPrice": gasPrice})
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
