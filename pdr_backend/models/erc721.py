from typing import Union
from web3.types import TxReceipt, HexBytes
from pdr_backend.util.contract import get_contract_abi
from pdr_backend.util.web3_config import Web3Config


class ERC721:
    def __init__(self, config: Web3Config, address: str):
        self.config = config
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("IERC721Template"),
        )

    def add_to_create_erc20_list(self, addr: str, wait_for_receipt=True) -> Union[HexBytes, TxReceipt]:
        gasPrice = self.config.w3.eth.gas_price
        tx = self.contract_instance.functions.addToCreateERC20List(addr).transact(
            {"from": self.config.owner, "gasPrice": gasPrice}
        )
        if not wait_for_receipt:
            return tx
        return self.config.w3.eth.wait_for_transaction_receipt(tx)
