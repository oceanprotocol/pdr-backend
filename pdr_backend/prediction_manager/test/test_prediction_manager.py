from web3.types import RPCEndpoint

from pdr_backend.conftest_ganache import *
from pdr_backend.contract.prediction_manager import (
    PredictionManager,
)  # pylint: disable=wildcard-import
from pdr_backend.prediction_manager.deploy import (
    deploy_prediction_manager_contract,
)
from pdr_backend.util.currency_types import Wei


def test_version(
    prediction_manager: PredictionManager,
):
    version = prediction_manager.version()
    assert version == "0.1.0", "Version should be 0.1.0"

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
    tx_receipt = prediction_manager.approve_ocean(contract_addrs, True)
    assert tx_receipt.status == 1, "Transaction failed"

    assert ocean_token.allowance(pm, pc1).amt_wei == 2**256 - 1
    assert ocean_token.allowance(pm, pc2).amt_wei == 2**256 - 1


def test_transfer_erc20(
    prediction_manager: PredictionManager, ocean_token, web3_config
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


def test_transfer(prediction_manager: PredictionManager, web3_config):
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


def test_submit_prediction_and_payout(
    prediction_manager: PredictionManager,
    web3_config,
    predictoor_contract: PredictoorContract,
    predictoor_contract2,
    ocean_token,
):
    # the user transfers 100 OCEAN tokens to the prediction manager
    ocean_token.transfer(
        prediction_manager.contract_address, Wei(100), web3_config.owner
    )

    # get the next prediction epoch
    current_epoch = predictoor_contract.get_current_epoch_ts()

    # set prediction epoch
    prediction_epoch = current_epoch + S_PER_EPOCH * 2

    # get the OCEAN balance of the contract before submitting
    bal_before = ocean_token.balanceOf(prediction_manager.contract_address)
    assert bal_before == Wei(
        100
    ), "OCEAN balance of the contract should be 100 before submitting"

    # submit prediction
    feeds = [
        predictoor_contract.contract_address,
        predictoor_contract2.contract_address,
    ]
    tx_receipt = prediction_manager.submit_prediction(
        stakes_up=[20, 30],
        stakes_down=[30, 20],
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

    # submit the trueval
    predictoor_contract.submit_trueval(
        True, prediction_epoch, False, True
    )  # submit True for the first contract
    predictoor_contract2.submit_trueval(
        False, prediction_epoch, False, True
    )  # submit False for the second contract

    # time to claim payouts
    # expected payouts are:
    # 20 OCEAN for the first contract
    # 20 OCEAN for the second contract
    # 40 Total

    # get the OCEAN balance of the contract before claiming
    bal_before = ocean_token.balanceOf(prediction_manager.contract_address)

    # claim
    prediction_manager.get_payout([prediction_epoch], feeds, wait_for_receipt=True)

    # get the OCEAN balance of the contract after claiming
    bal_after = ocean_token.balanceOf(prediction_manager.contract_address)

    assert bal_after == Wei(
        40
    ), "OCEAN balance of the contract should be 40 after claiming"


@pytest.fixture(scope="module")
def prediction_manager(web3_pp):
    contract_address = deploy_prediction_manager_contract(web3_pp)
    return PredictionManager(web3_pp, contract_address)
