import hashlib
import json
from typing import Union

from enforce_typing import enforce_types
from web3 import Web3
from web3.types import HexBytes, TxReceipt

from pdr_backend.contract.base_contract import BaseContract
from pdr_backend.util.networkutil import tx_call_params


@enforce_types
class DataNft(BaseContract):
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "ERC721Template")

    def set_data(self, field_label, field_value, wait_for_receipt=True):
        """Set key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label)  # to keccak256 hash
        field_value_bytes = field_value.encode()  # to array of bytes

        call_params = tx_call_params(self.web3_pp, gas=100000)
        tx = self.contract_instance.functions.setNewData(
            field_label_hash, field_value_bytes
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def add_erc20_deployer(self, address, wait_for_receipt=True):
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance.functions.addToCreateERC20List(
            self.config.w3.to_checksum_address(address)
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def set_ddo(self, ddo, wait_for_receipt=True):
        js = json.dumps(ddo)
        stored_ddo = Web3.to_bytes(text=js)
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance.functions.setMetaData(
            1,
            "",
            str(self.config.owner),
            bytes([0]),
            stored_ddo,
            Web3.to_bytes(hexstr=hashlib.sha256(js.encode("utf-8")).hexdigest()),
            [],
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def add_to_create_erc20_list(
        self, addr: str, wait_for_receipt=True
    ) -> Union[HexBytes, TxReceipt]:
        call_params = tx_call_params(self.web3_pp)
        tx = self.contract_instance.functions.addToCreateERC20List(addr).transact(
            call_params
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
