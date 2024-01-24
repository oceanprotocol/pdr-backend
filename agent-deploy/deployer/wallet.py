import json
import os
from typing import List
from attr import dataclass
from deployer.constants import KEY_FILE
from web3 import Web3
from enforce_typing import enforce_types


@dataclass
class Wallet:
    private_key: str

    def __str__(self):
        return self.private_key


@enforce_types
def generate_wallet() -> Wallet:
    w3 = Web3()
    wallet = w3.eth.account.create()
    print("Generated wallet with address: ", wallet.address)
    return Wallet(wallet._private_key.hex())


@enforce_types
def generate_wallets(n: int) -> List[Wallet]:
    return [generate_wallet() for _ in range(n)]


@enforce_types
def read_keys_json(config: str) -> List[Wallet]:
    if not os.path.exists(KEY_FILE):
        print(f"Key file {KEY_FILE} does not exist")
        return []
    with open(KEY_FILE, "r") as f:
        keys = json.load(f)[config]
    wallets = [Wallet(key) for key in keys]
    return wallets


@enforce_types
def generate_new_keys(config: str, n: int) -> List[Wallet]:
    wallets = read_keys_json(config)
    new_wallets = generate_wallets(n)
    wallets.extend(new_wallets)
    keys = {config: [str(wallet) for wallet in wallets]}
    print(f"Generated {n} new wallet(s) for {config} config")
    with open(KEY_FILE, "w") as f:
        json.dump(keys, f)
    return wallets
