from enforce_typing import enforce_types
import pytest

from pdr_backend.utils.contract import (
    is_sapphire_network,
    send_encrypted_tx,
    Web3Config,
    Token,
    PredictoorContract,
    FixedRate,
    get_contract_filename,
    )
from pdr_backend.utils.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)


TEST_RPC_URL = "http://127.0.0.1:8545"
TEST_PRIVATE_KEY = "0x1f4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209"


@enforce_types
def test_is_sapphire_network():
    assert not is_sapphire_network(0)
    assert is_sapphire_network(SAPPHIRE_TESTNET_CHAINID)
    assert is_sapphire_network(SAPPHIRE_MAINNET_CHAINID)


@enforce_types
def test_send_encrypted_tx():
    # FIXME
    pass


@enforce_types
def test_Web3Config_bad_rpc():
    with pytest.raises(ValueError):
        Web3Config(rpc_url=None, private_key=TEST_PRIVATE_KEY)

@enforce_types
def test_Web3Config_bad_key():
    with pytest.raises(ValueError):
        Web3Config(rpc_url=TEST_RPC_URL, private_key="foo")


@enforce_types
def test_Web3Config_happy_noPrivateKey():
    c = Web3Config(rpc_url=TEST_RPC_URL, private_key=None)
    
    assert c.w3 is not None
    assert not hasattr(c, "account")
    assert not hasattr(c, "owner")
    assert not hasattr(c, "private_key")


@enforce_types
def test_Web3Config_happy_havePrivateKey_noKeywords():
    c = Web3Config(TEST_RPC_URL, TEST_PRIVATE_KEY)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == TEST_PRIVATE_KEY


@enforce_types
def test_Web3Config_happy_havePrivateKey_withKeywords():
    c = Web3Config(rpc_url=TEST_RPC_URL, private_key=TEST_PRIVATE_KEY)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == TEST_PRIVATE_KEY

    
@enforce_types
def test_Token():
    config = Web3Config(TEST_RPC_URL, TEST_PRIVATE_KEY)
    #token_address = FIXME
    #token = Token(config, token_address)
