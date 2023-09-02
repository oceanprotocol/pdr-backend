from typing import Union

import hashlib
import json

from enforce_typing import enforce_types
from web3 import Web3
from web3.types import TxReceipt, HexBytes

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.util.web3_config import Web3Config


@enforce_types
class DataNft(BaseContract):
    def __init__(self, config: Web3Config, address: str):
        super().__init__(config, address, "ERC721Template")

    def set_data(self, field_label, field_value, wait_for_receipt=True):
        """Set key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label)  # to keccak256 hash
        field_value_bytes = field_value.encode()  # to array of bytes
        #        gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
            "gas": 100000,
        }
        tx = self.contract_instance.functions.setNewData(
            field_label_hash, field_value_bytes
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def add_erc20_deployer(self, address, wait_for_receipt=True):
        #        gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }
        tx = self.contract_instance.functions.addToCreateERC20List(
            self.config.w3.to_checksum_address(address)
        ).transact(call_params)
        if wait_for_receipt:
            self.config.w3.eth.wait_for_transaction_receipt(tx)
        return tx

    def set_ddo(self, ddo, wait_for_receipt=True):
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }
        js = json.dumps(ddo)
        stored_ddo = Web3.to_bytes(text=js)
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
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.addToCreateERC20List(addr).transact(
            {"from": self.config.owner, "gasPrice": gasPrice}
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
