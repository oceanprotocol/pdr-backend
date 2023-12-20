from enforce_typing import enforce_types
from pytest import approx

from pdr_backend.conftest_ganache import S_PER_EPOCH
from pdr_backend.contract.predictoor_contract import mock_predictoor_contract
from pdr_backend.contract.token import Token
from pdr_backend.util.contract import get_address
from pdr_backend.util.mathutil import from_wei, to_wei


@enforce_types
def test_get_id(predictoor_contract):
    id_ = predictoor_contract.getid()
    assert id_ == 3


@enforce_types
def test_is_valid_subscription_initially(predictoor_contract):
    is_valid_sub = predictoor_contract.is_valid_subscription()
    assert not is_valid_sub


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
def test_get_stake_token(predictoor_contract, web3_pp):
    stake_token = predictoor_contract.get_stake_token()
    ocean_address = get_address(web3_pp, "Ocean")
    assert stake_token == ocean_address


@enforce_types
def test_get_price(predictoor_contract):
    price = predictoor_contract.get_price()
    assert price / 1e18 == approx(3.603)


@enforce_types
def test_get_current_epoch(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch()
    now = predictoor_contract.config.get_block("latest").timestamp
    assert current_epoch == int(now // S_PER_EPOCH)


@enforce_types
def test_get_current_epoch_ts(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    now = predictoor_contract.config.get_block("latest").timestamp
    assert current_epoch == int(now // S_PER_EPOCH) * S_PER_EPOCH


@enforce_types
def test_get_seconds_per_epoch(predictoor_contract):
    seconds_per_epoch = predictoor_contract.get_secondsPerEpoch()
    assert seconds_per_epoch == S_PER_EPOCH


@enforce_types
def test_get_aggpredval(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    aggpredval = predictoor_contract.get_agg_predval(current_epoch)
    assert aggpredval == (0, 0)


@enforce_types
def test_soonest_timestamp_to_predict(predictoor_contract):
    current_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_timestamp = predictoor_contract.soonest_timestamp_to_predict(current_epoch)
    assert soonest_timestamp == current_epoch + S_PER_EPOCH * 2


@enforce_types
def test_get_trueValSubmitTimeout(predictoor_contract):
    trueValSubmitTimeout = predictoor_contract.get_trueValSubmitTimeout()
    assert trueValSubmitTimeout == 3 * 24 * 60 * 60


@enforce_types
def test_submit_prediction_trueval_payout(
    predictoor_contract,
    ocean_token: Token,
):
    OCEAN = ocean_token
    w3 = predictoor_contract.config.w3
    owner_addr = predictoor_contract.config.owner
    OCEAN_before = from_wei(OCEAN.balanceOf(owner_addr))
    cur_epoch = predictoor_contract.get_current_epoch_ts()
    soonest_ts = predictoor_contract.soonest_timestamp_to_predict(cur_epoch)
    predval = True
    stake_amt = 1.0
    receipt = predictoor_contract.submit_prediction(
        predval,
        stake_amt,
        soonest_ts,
        wait_for_receipt=True,
    )
    assert receipt["status"] == 1

    OCEAN_after = from_wei(OCEAN.balanceOf(owner_addr))
    assert (OCEAN_before - OCEAN_after) == approx(stake_amt, 1e-8)

    pred_tup = predictoor_contract.get_prediction(
        soonest_ts,
        predictoor_contract.config.owner,
    )
    assert pred_tup[0] == predval
    assert pred_tup[1] == to_wei(stake_amt)

    w3.provider.make_request("evm_increaseTime", [S_PER_EPOCH * 2])
    w3.provider.make_request("evm_mine", [])
    trueval = True
    receipt = predictoor_contract.submit_trueval(
        trueval,
        soonest_ts,
        cancel_round=False,
        wait_for_receipt=True,
    )
    assert receipt["status"] == 1

    receipt = predictoor_contract.payout(soonest_ts, wait_for_receipt=True)
    assert receipt["status"] == 1
    OCEAN_final = from_wei(OCEAN.balanceOf(owner_addr))
    assert OCEAN_before == approx(OCEAN_final, 2.0)  # + sub revenue


@enforce_types
def test_redeem_unused_slot_revenue(predictoor_contract):
    cur_epoch = predictoor_contract.get_current_epoch_ts() - S_PER_EPOCH * 123
    receipt = predictoor_contract.redeem_unused_slot_revenue(cur_epoch, True)
    assert receipt["status"] == 1


@enforce_types
def test_mock_predictoor_contract():
    c = mock_predictoor_contract("0x123", (3, 4))
    assert c.contract_address == "0x123"
    assert c.get_agg_predval() == (3, 4)
