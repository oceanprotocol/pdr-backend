# pylint: disable=redefined-outer-name
from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import
from pdr_backend.contract.dfrewards import DFRewards
from pdr_backend.contract.prediction_manager import (
    PredSubmitterManager,
)

from pdr_backend.util.currency_types import Wei
from pdr_backend.util.time_types import UnixTimeS


def test_version(
    prediction_manager: PredSubmitterManager,
):
    version = prediction_manager.version()
    assert version == "0.1.0", "Version should be 0.1.0"


def test_get_up_predictoor_address(
    prediction_manager: PredSubmitterManager,
):
    address = prediction_manager.predictoor_up_address()
    assert address


def test_get_down_predictoor_address(
    prediction_manager: PredSubmitterManager,
):
    address = prediction_manager.predictoor_down_address()
    assert address


def test_approve(
    prediction_manager: PredSubmitterManager,
    predictoor_contract1,
    predictoor_contract2,
    ocean_token,
):
    pmup = prediction_manager.predictoor_up_address()
    pmdown = prediction_manager.predictoor_down_address()
    pc1 = predictoor_contract1.contract_address
    pc2 = predictoor_contract2.contract_address
    assert ocean_token.allowance(pmup, pc1) == 0
    assert ocean_token.allowance(pmup, pc2) == 0
    assert ocean_token.allowance(pmdown, pc2) == 0
    assert ocean_token.allowance(pmdown, pc2) == 0

    contract_addrs = [
        pc1,
        pc2,
    ]
    tx_receipt = prediction_manager.approve_ocean(contract_addrs, True)
    assert tx_receipt.status == 1, "Transaction failed"

    assert ocean_token.allowance(pmup, pc1).amt_wei == 2**256 - 1
    assert ocean_token.allowance(pmup, pc2).amt_wei == 2**256 - 1
    assert ocean_token.allowance(pmdown, pc1).amt_wei == 2**256 - 1
    assert ocean_token.allowance(pmdown, pc2).amt_wei == 2**256 - 1


def test_transfer_erc20(
    prediction_manager: PredSubmitterManager, ocean_token, web3_config
):
    ocean_token.transfer(
        prediction_manager.contract_address, Wei(100), web3_config.owner
    )
    assert ocean_token.balanceOf(prediction_manager.contract_address) == Wei(100)
    before = ocean_token.balanceOf(web3_config.owner)
    prediction_manager.transfer_erc20(
        ocean_token.contract_address, web3_config.owner, Wei(100)
    )
    after = ocean_token.balanceOf(web3_config.owner)
    assert Wei(after.amt_wei - before.amt_wei) == Wei(100)
    assert ocean_token.balanceOf(prediction_manager.contract_address) == 0


def test_transfer(prediction_manager: PredSubmitterManager, web3_config):
    tx = web3_config.w3.eth.send_transaction(
        {
            "to": prediction_manager.contract_address,
            "value": 100,
            "gasPrice": web3_config.w3.eth.gas_price,
            "from": web3_config.owner,
        }
    )
    web3_config.w3.eth.wait_for_transaction_receipt(tx)
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 100
    before = web3_config.w3.eth.get_balance(web3_config.owner)
    prediction_manager.transfer()
    after = web3_config.w3.eth.get_balance(web3_config.owner)
    assert after - before == 100
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 0


def test_claim_dfrewards(
    prediction_manager: PredSubmitterManager, web3_pp, ocean_token
):
    dfrewards_addr = web3_pp.get_address("DFRewards")
    dfrewards = DFRewards(web3_pp, dfrewards_addr)

    pmup = prediction_manager.predictoor_up_address()
    pmdown = prediction_manager.predictoor_down_address()

    # approve rewards
    ocean_token.approve(dfrewards_addr, Wei(200), web3_pp.web3_config.owner)

    # allocate rewards
    tx = dfrewards.contract_instance.functions.allocate(
        [pmup, pmdown],
        [100, 100],
        ocean_token.contract_address,
    ).transact(web3_pp.tx_call_params())
    web3_pp.web3_config.w3.eth.wait_for_transaction_receipt(tx)

    # record before balances
    before_up = ocean_token.balanceOf(pmup)
    before_down = ocean_token.balanceOf(pmdown)

    # claim rewards
    prediction_manager.claim_dfrewards(ocean_token.contract_address, dfrewards_addr)

    # record after balances
    after_up = ocean_token.balanceOf(pmup)
    after_down = ocean_token.balanceOf(pmdown)

    # assert
    assert after_up - before_up == Wei(100)
    assert after_down - before_down == Wei(100)


def test_submit_prediction_and_payout(
    prediction_manager: PredSubmitterManager,
    web3_config,
    predictoor_contract1: PredictoorContract,
    predictoor_contract2,
    ocean_token,
):
    # the user transfers 100 OCEAN tokens to the prediction manager
    ocean_token.transfer(
        prediction_manager.contract_address, Wei(100), web3_config.owner
    )

    # get the next prediction epoch
    current_epoch = predictoor_contract1.get_current_epoch_ts()

    # set prediction epoch
    prediction_epoch = UnixTimeS(current_epoch + S_PER_EPOCH * 2)

    # get the OCEAN balance of the contract before submitting
    bal_before = ocean_token.balanceOf(prediction_manager.contract_address)
    assert bal_before == Wei(
        100
    ), "OCEAN balance of the contract should be 100 before submitting"

    feeds = [
        predictoor_contract1.contract_address,
        predictoor_contract2.contract_address,
    ]
    # give allowance
    tx_receipt = prediction_manager.approve_ocean(feeds)
    assert tx_receipt.status == 1, "Transaction failed"

    # submit prediction
    # first feed up 20, down 30
    # second feed up 40, down 10
    tx_receipt = prediction_manager.submit_prediction(
        stakes_up=[Wei(20), Wei(30)],
        stakes_down=[Wei(40), Wei(10)],
        feeds=feeds,
        epoch_start=prediction_epoch,
        wait_for_receipt=True,
    )
    assert tx_receipt.status == 1, "Transaction failed"

    # get the OCEAN balance of the contract after submitting
    bal_after = ocean_token.balanceOf(prediction_manager.contract_address)
    assert bal_after == 0, "OCEAN balance of the contract should be 0 after submitting"

    # fast forward time to get payout
    web3_config.w3.provider.make_request(
        RPCEndpoint("evm_increaseTime"), [S_PER_EPOCH * 4]
    )
    web3_config.w3.provider.make_request(RPCEndpoint("evm_mine"), [])

    # submit the trueval: True for first contract, False for second
    predictoor_contract1.submit_trueval(True, prediction_epoch, False, True)
    predictoor_contract2.submit_trueval(False, prediction_epoch, False, True)

    # time to claim payouts

    # get the OCEAN balance of the contract before claiming
    bal_before = ocean_token.balanceOf(prediction_manager.contract_address)

    # claim
    prediction_manager.get_payout([prediction_epoch], feeds, wait_for_receipt=True)

    # get the OCEAN balance of the contract after claiming
    bal_after = ocean_token.balanceOf(prediction_manager.contract_address)

    assert bal_after == Wei(
        100
    ), "OCEAN balance of the contract should be 100 after claiming"

    # check predictions one by one
    pmup = prediction_manager.predictoor_up_address()
    pmdown = prediction_manager.predictoor_down_address()

    pred_down_first_feed = predictoor_contract1.get_prediction(prediction_epoch, pmdown)
    pred_down_second_feed = predictoor_contract2.get_prediction(
        prediction_epoch, pmdown
    )
    pred_up_first_feed = predictoor_contract1.get_prediction(prediction_epoch, pmup)
    pred_up_second_feed = predictoor_contract2.get_prediction(prediction_epoch, pmup)

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
