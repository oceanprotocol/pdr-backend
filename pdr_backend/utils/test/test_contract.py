import time

from pdr_backend.publisher.publish import publish
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
    get_address,
)
from pdr_backend.utils.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)


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
def test_Web3Config_bad_rpc(private_key):
    with pytest.raises(ValueError):
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
def test_Web3Config_happy_havePrivateKey_noKeywords(rpc_url, private_key):
    c = Web3Config(rpc_url, private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Web3Config_happy_havePrivateKey_withKeywords(rpc_url, private_key):
    c = Web3Config(rpc_url=rpc_url, private_key=private_key)
    assert c.account
    assert c.owner == c.account.address
    assert c.private_key == private_key


@enforce_types
def test_Token(rpc_url, private_key, chain_id):
    config = Web3Config(rpc_url, private_key)
    token_address = get_address(chain_id, "Ocean")
    token = Token(config, token_address)

    accounts = config.w3.eth.accounts
    owner_addr = config.owner
    alice = accounts[1]

    token.contract_instance.functions.mint(owner_addr, 1000000000).transact(
        {"from": owner_addr, "gasPrice": config.w3.eth.gas_price}
    )

    allowance_start = token.allowance(owner_addr, alice)
    token.approve(alice, allowance_start + 100, True)
    time.sleep(5)
    allowance_end = token.allowance(owner_addr, alice)
    assert allowance_end - allowance_start == 100

    balance_start = token.balanceOf(alice)
    token.transfer(alice, 100, owner_addr)
    balance_end = token.balanceOf(alice)
    assert balance_end - balance_start == 100

@enforce_types
def test_PredictoorContract(rpc_url, private_key):
    config = Web3Config(rpc_url, private_key)
    owner = config.owner
    print("owner: ", owner)
    
    _, _, _,nft_addr= publish(
        s_per_epoch=300,
        s_per_subscription=300 * 24,
        base="ETH",
        quote="USDT",
        source="kraken",
        timeframe="5m",
        trueval_submitter_addr=owner,
        feeCollector_addr=owner,
        rate=3,
        cut=0.2,
        web3_config=config,
    )

    contract = PredictoorContract(config, nft_addr)

    id = contract.getid()
    assert id == 3

    is_valid_sub = contract.is_valid_subscription()
    assert is_valid_sub == False

    auth_sig = contract.get_auth_signature()
    assert "v" in auth_sig
    assert "r" in auth_sig
    assert "s" in auth_sig

    max_gas_limit = contract.get_max_gas()
    assert max_gas_limit == int(config.w3.eth.getBlock("latest").gasLimit * 0.99)

    receipt = contract.buy_and_start_subscription()
    assert receipt["status"] == 1
    
    is_valid_sub = contract.is_valid_subscription()
    assert is_valid_sub == True

    receipts = contract.buy_many(2, None, True)
    assert len(receipts) == 2

    

@pytest.fixture(autouse=True)
def run_before_each_test():
    # This setup code will be run before each test
    print("Setting up!")
