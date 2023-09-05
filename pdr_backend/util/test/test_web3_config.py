import os
from enforce_typing import enforce_types
import pytest

from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_Web3Config_bad_rpc():
    private_key = os.getenv("PRIVATE_KEY")
    with pytest.raises(ValueError):
        Web3Config(rpc_url=None, private_key=private_key)


@enforce_types
def test_Web3Config_bad_key():
    rpc_url = os.getenv("RPC_URL")
    with pytest.raises(ValueError):
        Web3Config(rpc_url=rpc_url, private_key="foo")


@enforce_types
def test_Web3Config_happy_noPrivateKey():
    rpc_url = os.getenv("RPC_URL")
    c = Web3Config(rpc_url=rpc_url, private_key=None)

    assert c.w3 is not None
    assert not hasattr(c, "account")
    assert not hasattr(c, "owner")
    assert not hasattr(c, "private_key")


@enforce_types
def test_Web3Config_happy_havePrivateKey_noKeywords():
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")
    c = Web3Config(rpc_url, private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Web3Config_happy_havePrivateKey_withKeywords():
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Web3Config_get_block_latest():
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    block = c.get_block("latest")
    assert block
    assert block["timestamp"] > 0


@enforce_types
def test_Web3Config_get_block_0():
    private_key = os.getenv("PRIVATE_KEY")
    rpc_url = os.getenv("RPC_URL")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    block = c.get_block(0)
    assert block
    assert block["timestamp"] > 0
