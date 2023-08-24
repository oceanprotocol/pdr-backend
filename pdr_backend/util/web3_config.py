from typing import Optional

from enforce_typing import enforce_types
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

@enforce_types
class Web3Config:
    def __init__(self, rpc_url: Optional[str], private_key: Optional[str]):
        self.rpc_url = rpc_url

        if rpc_url is None:
            raise ValueError("You must set RPC_URL variable")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            if not private_key.startswith("0x"):
                raise ValueError("Private key must start with 0x hex prefix")
            self.account: LocalAccount = Account.from_key(private_key)
            self.owner = self.account.address
            self.private_key = private_key
            self.w3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(self.account)
            )


