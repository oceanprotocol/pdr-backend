import time
from pdr_backend.publisher.publish import publish
from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.utils.contract import (
    is_sapphire_network,
    send_encrypted_tx,
    Web3Config,
    Token,
    PredictoorContract,
    FixedRate,
    get_contract_filename,
    get_address,
    get_contract_abi,
    get_addresses,
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
    utcnow = int(time.time())
    assert current_epoch == int(utcnow // 300)


def test_get_current_epoch_ts(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    utcnow = int(time.time())
    assert current_epoch == int(utcnow // 300) * 300


def test_get_seconds_per_epoch(predictoor_contract):
    seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
    assert seconds_per_epoch == 300


def test_get_aggpredval(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    aggpredval = predictoor_contract.get_agg_predval(current_epoch)
    assert aggpredval == 0


def test_soonest_timestamp_to_predict(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_timestamp = predictoor_contract.soonest_timestamp_to_predict(current_epoch)
    assert soonest_timestamp == current_epoch + 300 * 2


def test_get_trueValSubmitTimeout(predictoor_contract):
    trueValSubmitTimeout = predictoor_contract.get_trueValSubmitTimeout()
    assert trueValSubmitTimeout == 4 * 12 * 300


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
    assert balance_after - balance_before == 1e18

    prediction = predictoor_contract.get_prediction(
        soonest_timestamp, predictoor_contract.config.owner
    )
    assert prediction[0] == True
    assert prediction[1] == 1e18

    predictoor_contract.config.w3.provider.make_request("evm_increaseTime", [300 * 2])

    receipt = predictoor_contract.submit_trueval(
        True, soonest_timestamp, 0, False, True
    )
    assert receipt["status"] == 1

    receipt = predictoor_contract.payout(soonest_timestamp, True)
    assert receipt["status"] == 1
    balance_final = ocean_token.balanceOf(owner_addr)

    assert balance_before == balance_final


def test_redeem_unused_slot_revenue(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    receipt = predictoor_contract.redeem_unused_slot_revenue(current_epoch)
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


@pytest.fixture(autouse=True)
def run_before_each_test():
    # This setup code will be run before each test
    print("Setting up!")


@pytest.fixture(scope="module")
def predictoor_contract(rpc_url, private_key):
    config = Web3Config(rpc_url, private_key)
    _, _, _, _, logs = publish(
        s_per_epoch=300,
        s_per_subscription=300 * 24,
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
