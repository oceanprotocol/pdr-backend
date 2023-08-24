import os

import pytest

from pdr_backend.utils.contract import (
    Token,
    Web3Config,
    get_address,
)

_BARGE_ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"


@pytest.fixture(autouse=True)
def barge_address_file():
    os.environ["ADDRESS_FILE"] = os.path.expanduser(_BARGE_ADDRESS_FILE)


@pytest.fixture(scope="session")
def rpc_url():
    return os.environ.get("TEST_RPC_URL", default="http://127.0.0.1:8545")


@pytest.fixture(scope="session")
def private_key():
    return os.environ.get(
        "TEST_PRIVATE_KEY",
        default="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58",
    )


@pytest.fixture(scope="session")
def chain_id():
    return 8996


@pytest.fixture(scope="session")
def web3_config(rpc_url, private_key):
    return Web3Config(rpc_url, private_key)


@pytest.fixture(scope="session")
def ocean_token(web3_config, chain_id) -> Token:
    token_address = get_address(chain_id, "Ocean")
    return Token(web3_config, token_address)
