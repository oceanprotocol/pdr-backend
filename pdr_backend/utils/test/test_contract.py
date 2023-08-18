import os
import time
from pdr_backend.publisher.publish import publish
from enforce_typing import enforce_types
import pytest
from pytest import approx
from pathlib import Path
from unittest.mock import patch, Mock
from pdr_backend.utils.contract import (
    is_sapphire_network,
    send_encrypted_tx,
    ERC721Factory,
    FixedRate,
    Web3Config,
    Token,
    PredictoorContract,
    get_contract_filename,
    get_address,
    get_contract_abi,
    get_addresses,
)
from pdr_backend.utils.constants import (
    SAPPHIRE_TESTNET_CHAINID,
    SAPPHIRE_MAINNET_CHAINID,
)

SECONDS_PER_EPOCH = 300


@enforce_types
def test_is_sapphire_network():
    assert not is_sapphire_network(0)
    assert is_sapphire_network(SAPPHIRE_TESTNET_CHAINID)
    assert is_sapphire_network(SAPPHIRE_MAINNET_CHAINID)


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
    time.sleep(1)
    allowance_end = token.allowance(owner_addr, alice)
    assert allowance_end - allowance_start == 100

    balance_start = token.balanceOf(alice)
    token.transfer(alice, 100, owner_addr)
    balance_end = token.balanceOf(alice)
    assert balance_end - balance_start == 100


def test_get_id(predictoor_contract):
    id = predictoor_contract.getid()
    assert id == 3


def test_is_valid_subscription_initially(predictoor_contract):
    is_valid_sub = predictoor_contract.is_valid_subscription()
    assert is_valid_sub == False


def test_auth_signature(predictoor_contract):
    auth_sig = predictoor_contract.get_auth_signature()
    assert "v" in auth_sig
    assert "r" in auth_sig
    assert "s" in auth_sig


def test_max_gas_limit(predictoor_contract):
    max_gas_limit = predictoor_contract.get_max_gas()
    # You'll have access to the config object if required, using predictoor_contract.config
    expected_limit = int(
        predictoor_contract.config.w3.eth.get_block("latest").gasLimit * 0.99
    )
    assert max_gas_limit == expected_limit


def test_buy_and_start_subscription(predictoor_contract):
    receipt = predictoor_contract.buy_and_start_subscription()
    assert receipt["status"] == 1
    is_valid_sub = predictoor_contract.is_valid_subscription()
    assert is_valid_sub == True


def test_buy_many(predictoor_contract):
    receipts = predictoor_contract.buy_many(2, None, True)
    assert len(receipts) == 2


def test_get_exchanges(predictoor_contract):
    exchanges = predictoor_contract.get_exchanges()
    assert exchanges[0][0].startswith("0x")


def test_get_stake_token(predictoor_contract, web3_config):
    stake_token = predictoor_contract.get_stake_token()
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    assert stake_token == ocean_address


def test_get_price(predictoor_contract):
    price = predictoor_contract.get_price()
    assert price / 1e18 == approx(3.603)


def test_get_current_epoch(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch()
    now = predictoor_contract.config.w3.eth.get_block("latest").timestamp
    assert current_epoch == int(now // SECONDS_PER_EPOCH)


def test_get_current_epoch_ts(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    now = predictoor_contract.config.w3.eth.get_block("latest").timestamp
    assert current_epoch == int(now // SECONDS_PER_EPOCH) * SECONDS_PER_EPOCH


def test_get_seconds_per_epoch(predictoor_contract):
    seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
    assert seconds_per_epoch == SECONDS_PER_EPOCH


def test_get_aggpredval(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    aggpredval = predictoor_contract.get_agg_predval(current_epoch)
    assert aggpredval == 0


def test_soonest_timestamp_to_predict(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_timestamp = predictoor_contract.soonest_timestamp_to_predict(current_epoch)
    assert soonest_timestamp == current_epoch + SECONDS_PER_EPOCH * 2


def test_get_trueValSubmitTimeout(predictoor_contract):
    trueValSubmitTimeout = predictoor_contract.get_trueValSubmitTimeout()
    assert trueValSubmitTimeout == 4 * 12 * SECONDS_PER_EPOCH


def test_get_block(predictoor_contract):
    block = predictoor_contract.get_block(0)
    assert block.number == 0


def test_submit_prediction_aggpredval_payout(predictoor_contract, ocean_token: Token):
    owner_addr = predictoor_contract.config.owner
    balance_before = ocean_token.balanceOf(owner_addr)
    current_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_timestamp = predictoor_contract.soonest_timestamp_to_predict(current_epoch)
    receipt = predictoor_contract.submit_prediction(True, 1, soonest_timestamp, True)
    assert receipt["status"] == 1

    balance_after = ocean_token.balanceOf(owner_addr)
    assert balance_before - balance_after == 1e18

    prediction = predictoor_contract.get_prediction(
        soonest_timestamp, predictoor_contract.config.owner
    )
    assert prediction[0] == True
    assert prediction[1] == 1e18

    predictoor_contract.config.w3.provider.make_request(
        "evm_increaseTime", [SECONDS_PER_EPOCH * 2]
    )
    predictoor_contract.config.w3.provider.make_request("evm_mine", [])
    receipt = predictoor_contract.submit_trueval(
        True, soonest_timestamp, False, True
    )
    assert receipt["status"] == 1

    receipt = predictoor_contract.payout(soonest_timestamp, True)
    assert receipt["status"] == 1
    balance_final = ocean_token.balanceOf(owner_addr)
    assert balance_before / 1e18 == approx(balance_final / 1e18)  # + sub revenue


def test_redeem_unused_slot_revenue(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts() - SECONDS_PER_EPOCH * 123
    receipt = predictoor_contract.redeem_unused_slot_revenue(current_epoch, True)
    assert receipt["status"] == 1


@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        ("short", b"short" + b"0" * 27),
        ("this is exactly 32 chars", b"this is exactly 32 chars00000000"),
        (
            "this is a very long string which is more than 32 chars",
            b"this is a very long string which",
        ),
    ],
)
def test_string_to_bytes32(input_data, expected_output, predictoor_contract):
    result = predictoor_contract.string_to_bytes32(input_data)
    assert (
        result == expected_output
    ), f"For {input_data}, expected {expected_output}, but got {result}"


def test_get_address(chain_id):
    result = get_address(chain_id, "Ocean")
    assert result is not None


def test_get_addresses(chain_id):
    result = get_addresses(chain_id)
    assert result is not None


def test_get_contract_abi():
    result = get_contract_abi("ERC20Template3")
    assert len(result) > 0 and isinstance(result, list)


def test_get_contract_filename():
    result = get_contract_filename("ERC20Template3")
    assert result is not None and isinstance(result, Path)


def test_FixedRate(predictoor_contract, web3_config):
    exchanges = predictoor_contract.get_exchanges()
    address = exchanges[0][0]
    id = exchanges[0][1]
    print(exchanges)
    rate = FixedRate(web3_config, address)
    assert rate.get_dt_price(id)[0] / 1e18 == approx(3.603)


def test_ERC721Factory(web3_config):
    factory = ERC721Factory(web3_config)
    assert factory is not None

    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    fre_address = get_address(web3_config.w3.eth.chain_id, "FixedPrice")

    rate = 3
    cut = 0.2

    nft_data = ("TestToken", "TT", 1, "", True, web3_config.owner)
    erc_data = (
        3,
        ["ERC20Test", "ET"],
        [
            web3_config.owner,
            web3_config.owner,
            web3_config.owner,
            ocean_address,
            ocean_address,
        ],
        [2**256 - 1, 0, 300, 3000, 30000],
        [],
    )
    fre_data = (
        fre_address,
        [
            ocean_address,
            web3_config.owner,
            web3_config.owner,
            web3_config.owner,
        ],
        [
            18,
            18,
            web3_config.w3.to_wei(rate, "ether"),
            web3_config.w3.to_wei(cut, "ether"),
            1,
        ],
    )

    logs_nft, logs_erc = factory.createNftWithErc20WithFixedRate(
        nft_data, erc_data, fre_data
    )

    assert len(logs_nft) > 0
    assert len(logs_erc) > 0


def test_send_encrypted_tx(
    mock_send_encrypted_sapphire_tx, ocean_token, private_key, web3_config
):
    # Set up dummy return value for the mocked function
    mock_send_encrypted_sapphire_tx.return_value = (
        0,
        "dummy_tx_hash",
    )
    # Sample inputs for send_encrypted_tx
    function_name = "transfer"
    args = [web3_config.owner, 100]
    pk = private_key
    sender = web3_config.owner
    receiver = web3_config.w3.eth.accounts[1]
    rpc_url = "http://localhost:8545"
    value = 0
    gasLimit = 10000000
    gasCost = 0
    nonce = 0
    tx_hash, encrypted_data = send_encrypted_tx(
        ocean_token.contract_instance,
        function_name,
        args,
        pk,
        sender,
        receiver,
        rpc_url,
        value,
        gasLimit,
        gasCost,
        nonce,
    )
    assert tx_hash == 0
    assert encrypted_data == "dummy_tx_hash"
    mock_send_encrypted_sapphire_tx.assert_called_once_with(
        pk,
        sender,
        receiver,
        rpc_url,
        value,
        gasLimit,
        ocean_token.contract_instance.encodeABI(fn_name=function_name, args=args),
        gasCost,
        nonce,
    )


# --------------------


@pytest.fixture(autouse=True)
def run_before_each_test():
    # This setup code will be run before each test
    print("Setting up!")


@pytest.fixture(scope="module")
def predictoor_contract(rpc_url, private_key):
    config = Web3Config(rpc_url, private_key)
    _, _, _, _, logs = publish(
        s_per_epoch=SECONDS_PER_EPOCH,
        s_per_subscription=SECONDS_PER_EPOCH * 24,
        base="ETH",
        quote="USDT",
        source="kraken",
        timeframe="5m",
        trueval_submitter_addr=config.owner,
        feeCollector_addr=config.owner,
        rate=3,
        cut=0.2,
        web3_config=config,
    )
    dt_addr = logs["newTokenAddress"]
    return PredictoorContract(config, dt_addr)


@pytest.fixture
def mock_send_encrypted_sapphire_tx(monkeypatch):
    mock_function = Mock(return_value=(0, "dummy_tx_hash"))
    monkeypatch.setattr("sapphirepy.wrapper.send_encrypted_sapphire_tx", mock_function)
    return mock_function
