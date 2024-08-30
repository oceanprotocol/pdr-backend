#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from abc import ABC

from enforce_typing import enforce_types
from sapphirepy import wrapper


@enforce_types
class BaseContract(ABC):
    def __init__(self, web3_pp, address: str, contract_name: str):
        super().__init__()
        # pylint: disable=import-outside-toplevel
        from pdr_backend.ppss.web3_pp import Web3PP

        if not isinstance(web3_pp, Web3PP):
            raise ValueError(f"web3_pp is {web3_pp.__class__}, not Web3PP")
        self.web3_pp = web3_pp
        self.contract_address = self.config.w3.to_checksum_address(address)
        self.contract_instance = self.config.w3.eth.contract(
            address=self.config.w3.to_checksum_address(address),
            abi=web3_pp.get_contract_abi(contract_name),
        )
        self.contract_name = contract_name

    @property
    def config(self):
        return self.web3_pp.web3_config

    @property
    def name(self):
        return self.contract_name

    def send_encrypted_tx(
        self,
        function_name,
        args,
        sender=None,
        receiver=None,
        pk=None,
        value=0,  # in wei
        gasLimit=10000000,
        gasCost=0,  # in wei
        nonce=0,
    ) -> tuple:
        sender = self.config.owner if sender is None else sender
        receiver = self.contract_instance.address if receiver is None else receiver
        pk = self.config.account.key.hex()[2:] if pk is None else pk

        data = self.contract_instance.encode_abi(
            abi_element_identifier=function_name, args=args
        )
        rpc_url = self.config.rpc_url

        return wrapper.send_encrypted_sapphire_tx(
            pk,
            sender,
            receiver,
            rpc_url,
            value,
            gasLimit,
            data,
            gasCost,
            nonce,
        )

    def transact(
        self, function_name, params, call_params=None, use_wrapped_instance=False
    ):
        if not call_params:
            call_params = self.web3_pp.tx_call_params()

        instance = (
            self.contract_instance_wrapped
            if use_wrapped_instance
            else self.contract_instance
        )

        unsigned = getattr(instance.functions, function_name)(
            *params
        ).build_transaction(call_params)

        unsigned["nonce"] = self.config.w3.eth.get_transaction_count(
            call_params["from"]
        )
        signed = self.config.w3.eth.account.sign_transaction(
            unsigned, private_key=self.web3_pp.private_key
        )
        tx = self.config.w3.eth.send_raw_transaction(signed.raw_transaction)

        return tx
