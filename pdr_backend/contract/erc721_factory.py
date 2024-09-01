#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from web3.logs import DISCARD

from pdr_backend.contract.base_contract import BaseContract


@enforce_types
class Erc721Factory(BaseContract):
    def __init__(self, web3_pp):
        address = web3_pp.get_address("ERC721Factory")

        if not address:
            raise ValueError("Cannot figure out Erc721Factory address")

        super().__init__(web3_pp, address, "ERC721Factory")

    def createNftWithErc20WithFixedRate(self, NftCreateData, ErcCreateData, FixedData):
        call_params = self.web3_pp.tx_call_params()
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
