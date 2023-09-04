from typing import Optional, Union

from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.middleware import construct_sign_and_send_raw_middleware

from pdr_backend.util.constants import WEB3_MAX_TRIES


@enforce_types
class Web3Config:
    def __init__(
        self, rpc_url: Optional[str] = None, private_key: Optional[str] = None
    ):
        self.rpc_url = rpc_url

        if rpc_url is None:
            raise ValueError("You must set RPC_URL variable")

        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            self.account: LocalAccount = self.w3.eth.account.from_key(private_key)
            self.owner = self.account.address
            self.private_key = private_key
            self.w3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(self.account)
            )

    def get_block(
        self, block: Union[str, int], full_transactions: bool = False, tries: int = 0
    ):
        try:
            block = self.w3.eth.get_block(block)
            return block
        except Exception as e:
            print(f"An error occured while gettin block: {block}, error: {e}")
            if tries < WEB3_MAX_TRIES:
                print("Tryin again...")
                return self.get_block(block, full_transactions, tries + 1)
            raise Exception("Couldn't get block") from e
