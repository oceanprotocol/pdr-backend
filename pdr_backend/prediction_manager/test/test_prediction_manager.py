from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import *
from pdr_backend.contract.prediction_manager import (
    PredictionManager,
)  # pylint: disable=wildcard-import
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)


def test_approve(
    prediction_manager: PredictionManager,
    predictoor_contract,
    predictoor_contract2,
    ocean_token,
):
    pm = prediction_manager.contract_address
    pc1 = predictoor_contract.contract_address
    pc2 = predictoor_contract2.contract_address
    assert ocean_token.allowance(pm, pc1) == 0
    assert ocean_token.allowance(pm, pc2) == 0

    contract_addrs = [
        pc1,
        pc2,
    ]
    prediction_manager.approve_ocean(contract_addrs, True)

    assert ocean_token.allowance(pm, pc1) == 2**256 - 1
    assert ocean_token.allowance(pm, pc2) == 2**256 - 1


def test_transfer_erc20(
    prediction_manager: PredictionManager, ocean_token, web3_config
):
    ocean_token.transfer(prediction_manager.contract_address, 100)
    assert ocean_token.balance_of(prediction_manager.contract_address) == 100
    before = ocean_token.balance_of(web3_config.owner)
    prediction_manager.transfer_erc20(
        ocean_token.contract_address, web3_config.owner, 100
    )
    after = ocean_token.balance_of(web3_config.owner)
    assert after - before == 100
    assert ocean_token.balance_of(prediction_manager.contract_address) == 0


def test_transfer(prediction_manager: PredictionManager, web3_config):
    web3_config.w3.eth.send_transaction(
        {"to": prediction_manager.contract_address, "value": 100}
    )
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 100
    before = web3_config.w3.eth.get_balance(web3_config.owner)
    prediction_manager.transfer()
    after = web3_config.w3.eth.get_balance(web3_config.owner)
    assert after - before == 100
    assert web3_config.w3.eth.get_balance(prediction_manager.contract_address) == 0


def submit_prediction_and_payout(
    prediction_manager: PredictionManager,
    web3_config,
    predictoor_contract: PredictoorContract,
    predictoor_contract2,
    ocean_token,
):
    # the user transfers 100 OCEAN tokens to the prediction manager
    ocean_token.transfer(prediction_manager.contract_address, 100)

    # get the next prediction epoch
    current_epoch = predictoor_contract.get_current_epoch_ts()

    # set prediction epoch
    prediciton_epoch = current_epoch + S_PER_EPOCH * 2

    # get the OCEAN balance of the contract before submitting
    bal_before = ocean_token.balance_of(prediction_manager.contract_address)
    assert (
        bal_before == 100
    ), "OCEAN balance of the contract should be 100 before submitting"

    # submit prediction
    feeds = [
        predictoor_contract.contract_address,
        predictoor_contract2.contract_address,
    ]
    prediction_manager.submit_prediction(
        stakes_up=[20, 30],
        stakes_down=[30, 20],
        feeds=feeds,
        epoch=prediciton_epoch,
        wait_for_receipt=True,
    )

    # get the OCEAN balance of the contract after submitting
    bal_after = ocean_token.balance_of(prediction_manager.contract_address)
    assert bal_after == 0, "OCEAN balance of the contract should be 0 after submitting"

    # fast forward time to get payout
    web3_config.w3.provider.make_request(
        RPCEndpoint("evm_increaseTime"), [S_PER_EPOCH * 4]
    )
    web3_config.w3.provider.make_request(RPCEndpoint("evm_mine"), [])

    # submit the trueval
    predictoor_contract.submit_trueval(
        True, prediciton_epoch, False, True
    )  # submit True for the first contract
    predictoor_contract2.submit_trueval(
        False, prediciton_epoch, False, True
    )  # submit False for the second contract

    # time to claim payouts
    # expected payouts are:
    # 20 OCEAN for the first contract
    # 20 OCEAN for the second contract
    # 40 Total

    # get the OCEAN balance of the contract before claiming
    bal_before = ocean_token.balance_of(prediction_manager.contract_address)

    # claim
    prediction_manager.get_payout([prediciton_epoch], feeds, wait_for_receipt=True)

    # get the OCEAN balance of the contract after claiming
    bal_after = ocean_token.balance_of(prediction_manager.contract_address)

    assert bal_after == 40, "OCEAN balance of the contract should be 40 after claiming"


@pytest.fixture(scope="module")
def prediction_manager(web3_pp):
    return deploy_prediction_manager_contract(web3_pp)
