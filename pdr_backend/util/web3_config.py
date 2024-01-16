import time

from typing import Optional

from enforce_typing import enforce_types
from eth_account.signers.local import LocalAccount
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from eth_typing import BlockIdentifier
from web3 import Web3
from web3.middleware import (
    construct_sign_and_send_raw_middleware,
    http_retry_request_middleware,
)
from web3.types import BlockData

from pdr_backend.util.constants import WEB3_MAX_TRIES
from pdr_backend.util.constants import (
    SAPPHIRE_MAINNET_CHAINID,
    SAPPHIRE_TESTNET_CHAINID,
)

_KEYS = KeyAPI(NativeECCBackend)


@enforce_types
class Web3Config:
    def __init__(self, rpc_url: str, private_key: Optional[str] = None):
        self.rpc_url: str = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))

        if private_key is not None:
            self.account: LocalAccount = self.w3.eth.account.from_key(private_key)
            self.owner = self.account.address
            self.private_key = private_key
            self.w3.middleware_onion.add(
                construct_sign_and_send_raw_middleware(self.account)
            )
            self.w3.middleware_onion.add(http_retry_request_middleware)

    def get_block(
        self, block: BlockIdentifier, full_transactions: bool = False, tries: int = 0
    ) -> BlockData:
        try:
            block_data = self.w3.eth.get_block(block)
            return block_data
        except Exception as e:
            print(f"An error occured while getting block, error: {e}")
            if tries < WEB3_MAX_TRIES:
                print("Trying again...")
                # sleep times for the first 5 tries:
                # 2.5, 10.0, 22.5, 40.0, 62.5
                time.sleep(((tries + 1) / 2) ** (2) * 10)
                return self.get_block(block, full_transactions, tries + 1)
            raise Exception("Couldn't get block") from e

    def get_auth_signature(self):
        """
        @description
          Digitally sign

        @return
          auth -- dict with keys "userAddress", "v", "r", "s", "validUntil"
        """
        valid_until = self.get_block("latest").timestamp + 3600
        message_hash = self.w3.solidity_keccak(
            ["address", "uint256"],
            [self.owner, valid_until],
        )
        pk = _KEYS.PrivateKey(self.account.key)
        prefix = "\x19Ethereum Signed Message:\n32"
        signable_hash = self.w3.solidity_keccak(
            ["bytes", "bytes"],
            [
                self.w3.to_bytes(text=prefix),
                self.w3.to_bytes(message_hash),
            ],
        )
        signed = _KEYS.ecdsa_sign(message_hash=signable_hash, private_key=pk)
        auth = {
            "userAddress": self.owner,
            "v": (signed.v + 27) if signed.v <= 1 else signed.v,
            "r": self.w3.to_hex(self.w3.to_bytes(signed.r).rjust(32, b"\0")),
            "s": self.w3.to_hex(self.w3.to_bytes(signed.s).rjust(32, b"\0")),
            "validUntil": valid_until,
        }
        return auth

    @property
    def is_sapphire(self):
        return self.w3.eth.chain_id in [
            SAPPHIRE_TESTNET_CHAINID,
            SAPPHIRE_MAINNET_CHAINID,
        ]

    @enforce_types
    def get_max_gas(self) -> int:
        """Returns max block gas"""
        block = self.get_block(self.w3.eth.block_number, full_transactions=False)
        return int(block["gasLimit"] * 0.99)

    @enforce_types
    def get_current_timestamp(self):
        """Returns latest block"""
        return self.get_block("latest")["timestamp"]
