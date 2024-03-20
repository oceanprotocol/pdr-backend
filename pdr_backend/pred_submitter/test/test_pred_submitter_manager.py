# pylint: disable=redefined-outer-name
from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.contract.pred_submitter_mgr import (
    PredSubmitterMgr,
)

from pdr_backend.util.currency_types import Wei
from pdr_backend.util.time_types import UnixTimeS


def test_version(
    pred_submitter_mgr: PredSubmitterMgr,
):
    version = pred_submitter_mgr.version()
    assert version == "0.1.0", "Version should be 0.1.0"


def test_get_up_predictoor_address(
    pred_submitter_mgr: PredSubmitterMgr,
):
    address = pred_submitter_mgr.predictoor_up_address()
    assert address


def test_get_down_predictoor_address(
    pred_submitter_mgr: PredSubmitterMgr,
):
    address = pred_submitter_mgr.predictoor_down_address()
    assert address


def test_approve(
    pred_submitter_mgr: PredSubmitterMgr,
    feed_contract1,
    feed_contract2,
    OCEAN,
):
    pmup = pred_submitter_mgr.predictoor_up_address()
    pmdown = pred_submitter_mgr.predictoor_down_address()
    pc1 = feed_contract1.contract_address
    pc2 = feed_contract2.contract_address
    assert OCEAN.allowance(pmup, pc1) == 0
    assert OCEAN.allowance(pmup, pc2) == 0
    assert OCEAN.allowance(pmdown, pc2) == 0
    assert OCEAN.allowance(pmdown, pc2) == 0

    contract_addrs = [
        pc1,
        pc2,
    ]
    tx_receipt = pred_submitter_mgr.approve_ocean(contract_addrs, True)
    assert tx_receipt.status == 1, "Transaction failed"

    assert OCEAN.allowance(pmup, pc1).amt_wei == 2**256 - 1
    assert OCEAN.allowance(pmup, pc2).amt_wei == 2**256 - 1
    assert OCEAN.allowance(pmdown, pc1).amt_wei == 2**256 - 1
    assert OCEAN.allowance(pmdown, pc2).amt_wei == 2**256 - 1


def test_transfer_erc20(pred_submitter_mgr: PredSubmitterMgr, OCEAN, web3_config):
    OCEAN.transfer(pred_submitter_mgr.contract_address, Wei(100), web3_config.owner)
    assert OCEAN.balanceOf(pred_submitter_mgr.contract_address) == Wei(100)
    before = OCEAN.balanceOf(web3_config.owner)
    pred_submitter_mgr.transfer_erc20(
        OCEAN.contract_address, web3_config.owner, Wei(100)
    )
    after = OCEAN.balanceOf(web3_config.owner)
    assert Wei(after.amt_wei - before.amt_wei) == Wei(100)
    assert OCEAN.balanceOf(pred_submitter_mgr.contract_address) == 0


def test_transfer(pred_submitter_mgr: PredSubmitterMgr, web3_config):
    tx = web3_config.w3.eth.send_transaction(
        {
            "to": pred_submitter_mgr.contract_address,
            "value": 100,
            "gasPrice": web3_config.w3.eth.gas_price,
            "from": web3_config.owner,
        }
    )
    web3_config.w3.eth.wait_for_transaction_receipt(tx)
    assert web3_config.w3.eth.get_balance(pred_submitter_mgr.contract_address) == 100
    before = web3_config.w3.eth.get_balance(web3_config.owner)
    pred_submitter_mgr.transfer()
    after = web3_config.w3.eth.get_balance(web3_config.owner)
    assert after - before == 100
    assert web3_config.w3.eth.get_balance(pred_submitter_mgr.contract_address) == 0


def test_claim_dfrewards(pred_submitter_mgr: PredSubmitterMgr, web3_pp, OCEAN):
    dfrewards_addr = web3_pp.get_address("DFRewards")
    dfrewards = DFRewards(web3_pp, dfrewards_addr)

    pmup = pred_submitter_mgr.predictoor_up_address()
    pmdown = pred_submitter_mgr.predictoor_down_address()

    # approve rewards
    OCEAN.approve(dfrewards_addr, Wei(200), web3_pp.web3_config.owner)

    # allocate rewards
    tx = dfrewards.contract_instance.functions.allocate(
        [pmup, pmdown],
        [100, 100],
        OCEAN.contract_address,
    ).transact(web3_pp.tx_call_params())
    web3_pp.web3_config.w3.eth.wait_for_transaction_receipt(tx)

    # record before balances
    before_up = OCEAN.balanceOf(pmup)
    before_down = OCEAN.balanceOf(pmdown)

    # claim rewards
    pred_submitter_mgr.claim_dfrewards(OCEAN.contract_address, dfrewards_addr)

    # record after balances
    after_up = OCEAN.balanceOf(pmup)
    after_down = OCEAN.balanceOf(pmdown)

    # assert
    assert after_up - before_up == Wei(100)
    assert after_down - before_down == Wei(100)


def test_submit_prediction_and_payout(
    pred_submitter_mgr: PredSubmitterMgr,
    web3_config,
    feed_contract1: FeedContract,
    feed_contract2,
    OCEAN,
):
    # the user transfers 100 OCEAN tokens to the prediction manager
    OCEAN.transfer(pred_submitter_mgr.contract_address, Wei(100), web3_config.owner)

    # get the next prediction epoch
    current_epoch = feed_contract1.get_current_epoch_ts()

    # set prediction epoch
    prediction_epoch = UnixTimeS(current_epoch + S_PER_EPOCH * 2)

    # get the OCEAN balance of the contract before submitting
    bal_before = OCEAN.balanceOf(pred_submitter_mgr.contract_address)
    assert bal_before == Wei(
        100
    ), "OCEAN balance of the contract should be 100 before submitting"

    feeds = [
        feed_contract1.contract_address,
        feed_contract2.contract_address,
    ]
    # give allowance
    tx_receipt = pred_submitter_mgr.approve_ocean(feeds)
    assert tx_receipt.status == 1, "Transaction failed"

    # submit prediction
    # first feed up 20, down 30
    # second feed up 40, down 10
    tx_receipt = pred_submitter_mgr.submit_prediction(
        stakes_up=[Wei(20), Wei(30)],
        stakes_down=[Wei(40), Wei(10)],
        feeds=feeds,
        epoch=prediction_epoch,
        wait_for_receipt=True,
    )
    assert tx_receipt.status == 1, "Transaction failed"

    # get the OCEAN balance of the contract after submitting
    bal_after = OCEAN.balanceOf(pred_submitter_mgr.contract_address)
    assert bal_after == 0, "OCEAN balance of the contract should be 0 after submitting"

    # fast forward time to get payout
    web3_config.w3.provider.make_request(
        RPCEndpoint("evm_increaseTime"), [S_PER_EPOCH * 4]
    )
    web3_config.w3.provider.make_request(RPCEndpoint("evm_mine"), [])

    # submit the trueval: True for first contract, False for second
    feed_contract1.submit_trueval(True, prediction_epoch, False, True)
    feed_contract2.submit_trueval(False, prediction_epoch, False, True)

    # time to claim payouts

    # get the OCEAN balance of the contract before claiming
    bal_before = OCEAN.balanceOf(pred_submitter_mgr.contract_address)

    # claim
    pred_submitter_mgr.get_payout([prediction_epoch], feeds, wait_for_receipt=True)

    # get the OCEAN balance of the contract after claiming
    bal_after = OCEAN.balanceOf(pred_submitter_mgr.contract_address)

    assert bal_after == Wei(
        100
    ), "OCEAN balance of the contract should be 100 after claiming"

    # check predictions one by one
    pmup = pred_submitter_mgr.predictoor_up_address()
    pmdown = pred_submitter_mgr.predictoor_down_address()

    pred_down_first_feed = feed_contract1.get_prediction(prediction_epoch, pmdown)
    pred_down_second_feed = feed_contract2.get_prediction(
        prediction_epoch, pmdown
    )
    pred_up_first_feed = feed_contract1.get_prediction(prediction_epoch, pmup)
    pred_up_second_feed = feed_contract2.get_prediction(prediction_epoch, pmup)

    assert pred_down_first_feed == (
        False,
        40,
        pmdown,
        True,
    ), "Prediction should be False, 30"
    assert pred_down_second_feed == (
        False,
        10,
        pmdown,
        True,
    ), "Prediction should be True, 10"
    assert pred_up_first_feed == (
        True,
        20,
        pmup,
        True,
    ), "Prediction should be False, 20"
    assert pred_up_second_feed == (
        True,
        30,
        pmup,
        True,
    ), "Prediction should be True, 40"
