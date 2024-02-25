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

        data = self.contract_instance.encodeABI(fn_name=function_name, args=args)
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
