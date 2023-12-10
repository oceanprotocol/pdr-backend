from typing import List
from unittest.mock import Mock

from enforce_typing import enforce_types
from eth_typing import ChecksumAddress

from pdr_backend.models.base_contract import BaseContract
from pdr_backend.ppss.web3_pp import Web3PP


class PredictoorBatcher(BaseContract):
    @enforce_types
    def __init__(self, web3_pp, address: str):
        super().__init__(web3_pp, address, "PredictoorHelper")

    @property
    def web3_config(self):
        return self.web3_pp.web3_config

    @property
    def w3(self):
        return self.web3_config.w3

    @property
    def gas_price(self):
        return self.w3.eth.gas_price

    @enforce_types
    def consume_multiple(
        self,
        addresses: List[ChecksumAddress],
        times: List[int],
        token_addr: str,
        wait_for_receipt=True,
    ):
        tx = self.contract_instance.functions.consumeMultiple(
            addresses, times, token_addr
        ).transact(
            {
                "from": self.web3_config.owner,
                "gasPrice": self.gas_price,
                "gas": 14_000_000,
            }
        )
        if not wait_for_receipt:
            return tx
        return self.w3.eth.wait_for_transaction_receipt(tx)

    @enforce_types
    def submit_truevals_contracts(
        self,
        contract_addrs: List[ChecksumAddress],
        epoch_starts: List[List[int]],
        trueVals: List[List[bool]],
        cancelRounds: List[List[bool]],
        wait_for_receipt=True,
    ):
        tx = self.contract_instance.functions.submitTruevalContracts(
            contract_addrs, epoch_starts, trueVals, cancelRounds
        ).transact({"from": self.web3_config.owner, "gasPrice": self.gas_price})
        if not wait_for_receipt:
            return tx
        return self.w3.eth.wait_for_transaction_receipt(tx)

    @enforce_types
    def submit_truevals(
        self,
        contract_addr: ChecksumAddress,
        epoch_starts: List[int],
        trueVals: List[bool],
        cancelRounds: List[bool],
        wait_for_receipt=True,
    ):
        tx = self.contract_instance.functions.submitTruevals(
            contract_addr, epoch_starts, trueVals, cancelRounds
        ).transact({"from": self.web3_config.owner, "gasPrice": self.gas_price})
        if not wait_for_receipt:
            return tx
        return self.w3.eth.wait_for_transaction_receipt(tx)


# =========================================================================
# utilities for testing


@enforce_types
def mock_predictoor_batcher(web3_pp: Web3PP) -> PredictoorBatcher:
    b = Mock(spec=PredictoorBatcher)
    b.web3_pp = web3_pp
    b.contract_address = "0xPdrBatcherAddr"
    return b
