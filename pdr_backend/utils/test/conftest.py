import os
import pytest


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
