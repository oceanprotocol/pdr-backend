import os

import pytest
from enforce_typing import enforce_types

from pdr_backend.util.constants import MAX_UINT
from pdr_backend.util.web3_config import Web3Config


@enforce_types
def test_Web3Config_bad_rpc():
    private_key = os.getenv("PRIVATE_KEY")
    with pytest.raises(TypeError):
        Web3Config(rpc_url=None, private_key=private_key)


@enforce_types
def test_Web3Config_bad_key(rpc_url):
    with pytest.raises(ValueError):
        Web3Config(rpc_url=rpc_url, private_key="foo")


@enforce_types
def test_Web3Config_happy_noPrivateKey(rpc_url):
    c = Web3Config(rpc_url=rpc_url, private_key=None)

    assert c.w3 is not None
    assert not hasattr(c, "account")
    assert not hasattr(c, "owner")
    assert not hasattr(c, "private_key")


@enforce_types
def test_Web3Config_happy_havePrivateKey_noKeywords(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    c = Web3Config(rpc_url, private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Web3Config_happy_havePrivateKey_withKeywords(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Web3Config_get_block_latest(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    block = c.get_block("latest")
    assert block
    assert block["timestamp"] > 0


@enforce_types
def test_Web3Config_get_block_0(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    block = c.get_block(0)
    assert block
    assert block["timestamp"] > 0


@enforce_types
def test_Web3Config_get_auth_signature(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    auth = c.get_auth_signature()

    # just a super basic test
    assert sorted(auth.keys()) == sorted(["userAddress", "v", "r", "s", "validUntil"])


@enforce_types
def test_get_max_gas(rpc_url):
    private_key = os.getenv("PRIVATE_KEY")
    web3_config = Web3Config(rpc_url=rpc_url, private_key=private_key)
    max_gas = web3_config.get_max_gas()
    assert 0 < max_gas < MAX_UINT

    target_max_gas = int(web3_config.get_block("latest").gasLimit * 0.99)
    assert max_gas == target_max_gas
