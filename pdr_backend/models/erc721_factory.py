from enforce_typing import enforce_types
from web3.logs import DISCARD

from pdr_backend.util.contract import get_address, get_contract_abi
from pdr_backend.util.web3_config import Web3Config

@enforce_types
class ERC721Factory:
    def __init__(self, config: Web3Config, chain_id=None):
        if not chain_id:
            chain_id = config.w3.eth.chain_id
        address = get_address(chain_id, "ERC721Factory")
        if not address:
            raise ValueError("Cannot figure out ERC721Factory address")
        self.contract_address = config.w3.to_checksum_address(address)
        self.contract_instance = config.w3.eth.contract(
            address=config.w3.to_checksum_address(address),
            abi=get_contract_abi("ERC721Factory"),
        )
        self.config = config

    def createNftWithErc20WithFixedRate(self, NftCreateData, ErcCreateData, FixedData):
        #            gasPrice = self.config.w3.eth.gas_price
        call_params = {
            "from": self.config.owner,
            "gasPrice": 100000000000,
        }

        tx = self.contract_instance.functions.createNftWithErc20WithFixedRate(
            NftCreateData, ErcCreateData, FixedData
        ).transact(call_params)
        receipt = self.config.w3.eth.wait_for_transaction_receipt(tx)
        if receipt["status"] != 1:
            raise ValueError(f"createNftWithErc20WithFixedRate failed in {tx.hex()}")
        # print(receipt)
        logs_nft = self.contract_instance.events.NFTCreated().process_receipt(
            receipt, errors=DISCARD
        )
        logs_erc = self.contract_instance.events.TokenCreated().process_receipt(
            receipt, errors=DISCARD
        )
        return logs_nft[0]["args"], logs_erc[0]["args"]


