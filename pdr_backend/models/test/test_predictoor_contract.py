from enforce_typing import enforce_types
import pytest
from pytest import approx

from pdr_backend.conftest_ganache import SECONDS_PER_EPOCH
from pdr_backend.models.token import Token
from pdr_backend.util.contract import get_address


@enforce_types
def test_get_id(predictoor_contract):
    id_ = predictoor_contract.getid()
    assert id_ == 3


@enforce_types
def test_is_valid_subscription_initially(predictoor_contract):
    is_valid_sub = predictoor_contract.is_valid_subscription()
    assert not is_valid_sub


@enforce_types
def test_auth_signature(predictoor_contract):
    auth_sig = predictoor_contract.get_auth_signature()
    assert "v" in auth_sig
    assert "r" in auth_sig
    assert "s" in auth_sig


@enforce_types
def test_max_gas_limit(predictoor_contract):
    max_gas_limit = predictoor_contract.get_max_gas()
    # You'll have access to the config object if required, using predictoor_contract.config
    expected_limit = int(predictoor_contract.config.get_block("latest").gasLimit * 0.99)
    assert max_gas_limit == expected_limit


@enforce_types
def test_buy_and_start_subscription(predictoor_contract):
    receipt = predictoor_contract.buy_and_start_subscription()
    assert receipt["status"] == 1
    is_valid_sub = predictoor_contract.is_valid_subscription()
    assert is_valid_sub


@enforce_types
def test_buy_many(predictoor_contract):
    receipts = predictoor_contract.buy_many(2, None, True)
    assert len(receipts) == 2


@enforce_types
def test_get_exchanges(predictoor_contract):
    exchanges = predictoor_contract.get_exchanges()
    assert exchanges[0][0].startswith("0x")


@enforce_types
def test_get_stake_token(predictoor_contract, web3_config):
    stake_token = predictoor_contract.get_stake_token()
    ocean_address = get_address(web3_config.w3.eth.chain_id, "Ocean")
    assert stake_token == ocean_address


@enforce_types
def test_get_price(predictoor_contract):
    price = predictoor_contract.get_price()
    assert price / 1e18 == approx(3.603)


@enforce_types
def test_get_current_epoch(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch()
    now = predictoor_contract.config.get_block("latest").timestamp
    assert current_epoch == int(now // SECONDS_PER_EPOCH)


def test_get_current_epoch_ts(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    now = predictoor_contract.config.get_block("latest").timestamp
    assert current_epoch == int(now // SECONDS_PER_EPOCH) * SECONDS_PER_EPOCH


@enforce_types
def test_get_seconds_per_epoch(predictoor_contract):
    seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
    assert seconds_per_epoch == SECONDS_PER_EPOCH


@enforce_types
def test_get_aggpredval(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    aggpredval = predictoor_contract.get_agg_predval(current_epoch)
    assert aggpredval == (0, 0)


@enforce_types
def test_soonest_timestamp_to_predict(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_timestamp = predictoor_contract.soonest_timestamp_to_predict(current_epoch)
    assert soonest_timestamp == current_epoch + SECONDS_PER_EPOCH * 2


@enforce_types
def test_get_trueValSubmitTimeout(predictoor_contract):
    trueValSubmitTimeout = predictoor_contract.get_trueValSubmitTimeout()
    assert trueValSubmitTimeout == 3 * 24 * 60 * 60


@enforce_types
def test_get_block(predictoor_contract):
    block = predictoor_contract.get_block(0)
    assert block.number == 0


@enforce_types
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
    assert prediction[0]
    assert prediction[1] == 1e18

    predictoor_contract.config.w3.provider.make_request(
        "evm_increaseTime", [SECONDS_PER_EPOCH * 2]
    )
    predictoor_contract.config.w3.provider.make_request("evm_mine", [])
    receipt = predictoor_contract.submit_trueval(True, soonest_timestamp, False, True)
    assert receipt["status"] == 1

    receipt = predictoor_contract.payout(soonest_timestamp, True)
    assert receipt["status"] == 1
    balance_final = ocean_token.balanceOf(owner_addr)
    assert balance_before / 1e18 == approx(balance_final / 1e18)  # + sub revenue


@enforce_types
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
