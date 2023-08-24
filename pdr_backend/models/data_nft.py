from enforce_typing import enforce_types
import hashlib
import json

from pdr_backend.util.web3_config import Web3Config
from pdr_backend.util.contract import get_contract_abi

@enforce_types
class DataNft:
    def __init__(self, config: Web3Config, address: str):
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC721Template"),
        )
        self.config = config

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
        #        gasPrice = self.config.w3.eth.gas_price
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

